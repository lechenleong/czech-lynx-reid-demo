from __future__ import annotations

import base64
import hashlib
import json
import random
import time
from pathlib import Path

import streamlit as st


ROOT = Path(__file__).parent
DATA_FILE = ROOT / "data" / "lynx_demo.json"
ROUND_SIZE = 3
REFERENCE_CHOICES = 4


st.set_page_config(
    page_title="CzechLynx Recognition (a simulated AI demo)",
    page_icon=":mag:",
    layout="wide",
    initial_sidebar_state="expanded",
)


def load_demo() -> dict:
    if not DATA_FILE.exists():
        st.error(f"Missing demo manifest: {DATA_FILE}")
        st.stop()
    with DATA_FILE.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def asset_path(path_value: str) -> Path:
    path = Path(path_value)
    if not path.is_absolute():
        path = ROOT / path
    return path


def image_markup(path_value: str, alt: str, max_height: int = 320) -> str:
    path = asset_path(path_value)
    if not path.exists():
        return (
            f'<div class="missing-image" style="min-height:{max_height}px">'
            f"<strong>Image missing</strong><span>{path_value}</span></div>"
        )

    mime = {
        ".svg": "image/svg+xml",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }.get(path.suffix.lower(), "application/octet-stream")
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return (
        f'<img class="lynx-image" src="data:{mime};base64,{encoded}" '
        f'alt="{alt}" style="max-height:{max_height}px" />'
    )


def identity_by_id(demo: dict) -> dict[str, dict]:
    return {item["id"]: item for item in demo["identities"]}


def stable_score(query_id: str, identity_id: str) -> int:
    digest = hashlib.sha256(f"{query_id}:{identity_id}".encode("utf-8")).hexdigest()
    return 46 + (int(digest[:6], 16) % 32)


def ranked_scores(query: dict, identities: list[dict]) -> list[tuple[str, int]]:
    correct_id = query["correct_identity"]
    confidence = int(query.get("confidence", 96))
    scores = []
    for identity in identities:
        identity_id = identity["id"]
        score = confidence if identity_id == correct_id else stable_score(query["id"], identity_id)
        scores.append((identity_id, score))
    return sorted(scores, key=lambda item: item[1], reverse=True)


def build_reference_choices(query: dict, demo: dict) -> list[str]:
    all_identity_ids = [identity["id"] for identity in demo["identities"]]
    correct_id = query["correct_identity"]

    candidate_ids = query.get("reference_choices", all_identity_ids)
    candidate_ids = [identity_id for identity_id in candidate_ids if identity_id in all_identity_ids]
    if correct_id not in candidate_ids:
        candidate_ids.append(correct_id)

    distractors = [identity_id for identity_id in candidate_ids if identity_id != correct_id]
    needed = max(0, REFERENCE_CHOICES - 1)

    if len(distractors) < needed:
        extra_pool = [
            identity_id
            for identity_id in all_identity_ids
            if identity_id != correct_id and identity_id not in distractors
        ]
        distractors.extend(random.sample(extra_pool, min(len(extra_pool), needed - len(distractors))))

    chosen = [correct_id] + random.sample(distractors, min(len(distractors), needed))
    random.shuffle(chosen)
    return chosen


def create_random_round(demo: dict) -> None:
    all_queries = demo["queries"]
    round_queries = random.sample(all_queries, min(ROUND_SIZE, len(all_queries)))

    for query in all_queries:
        st.session_state.pop(f"guess_{query['id']}", None)

    reference_choices = {
        query["id"]: build_reference_choices(query, demo) for query in round_queries
    }
    st.session_state["active_query_ids"] = [query["id"] for query in round_queries]
    st.session_state["reference_choices"] = reference_choices
    st.session_state["guesses"] = {
        query["id"]: reference_choices[query["id"]][0] for query in round_queries
    }


def active_queries(demo: dict) -> list[dict]:
    query_by_id = {query["id"]: query for query in demo["queries"]}
    query_ids = st.session_state.get("active_query_ids", [])
    return [query_by_id[query_id] for query_id in query_ids if query_id in query_by_id]


def reference_identities_for_query(query: dict, demo: dict) -> list[dict]:
    by_id = identity_by_id(demo)
    choice_ids = st.session_state.get("reference_choices", {}).get(query["id"])
    if not choice_ids:
        choice_ids = build_reference_choices(query, demo)
        st.session_state.setdefault("reference_choices", {})[query["id"]] = choice_ids
    return [by_id[identity_id] for identity_id in choice_ids if identity_id in by_id]


def initialize_state(demo: dict) -> None:
    defaults = {
        "revealed": False,
        "analysis_ran": False,
        "guesses": {},
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)

    if not st.session_state.get("active_query_ids"):
        create_random_round(demo)


def reset_demo(demo: dict) -> None:
    st.session_state["revealed"] = False
    st.session_state["analysis_ran"] = False
    create_random_round(demo)


def render_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --ink: #17201a;
            --muted: #66736d;
            --leaf: #2d6a4f;
            --moss: #588157;
            --clay: #b36b45;
            --sun: #f5b84b;
            --paper: #fbfaf5;
            --line: rgba(23, 32, 26, 0.16);
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1240px;
        }

        h1, h2, h3 {
            color: var(--ink);
            letter-spacing: 0;
        }

        .hero {
            padding: 1.25rem 0 0.75rem;
            border-bottom: 1px solid var(--line);
            margin-bottom: 1rem;
        }

        .hero p {
            max-width: 820px;
            color: var(--muted);
            font-size: 1.05rem;
            line-height: 1.55;
        }

        .lynx-card {
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 0.75rem;
            background: var(--paper);
            min-height: 100%;
        }

        .lynx-card h4 {
            margin: 0.45rem 0 0.1rem;
            color: var(--ink);
            font-size: 1rem;
        }

        .lynx-card p, .small-note {
            color: var(--muted);
            font-size: 0.9rem;
            line-height: 1.45;
        }

        .comparison-card {
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 0.85rem;
            background: #fffdf8;
            margin-bottom: 1rem;
        }

        .comparison-card h3 {
            margin-top: 0;
        }

        .mystery-panel {
            border: 1px solid rgba(23, 32, 26, 0.18);
            border-radius: 8px;
            background: var(--paper);
            padding: 0.75rem;
        }

        .reference-option {
            border: 1px solid rgba(23, 32, 26, 0.16);
            border-radius: 8px;
            background: #fbfaf5;
            padding: 0.7rem;
            min-height: 100%;
        }

        .reference-option.selected {
            border-color: var(--leaf);
            box-shadow: 0 0 0 2px rgba(45, 106, 79, 0.18);
            background: #f1f8ef;
        }

        .reference-option h4 {
            margin: 0.4rem 0 0.15rem;
            color: var(--ink);
            font-size: 0.95rem;
        }

        .reference-option p {
            margin: 0;
            color: var(--muted);
            font-size: 0.78rem;
            line-height: 1.35;
        }

        .selected-label {
            color: var(--leaf);
            font-weight: 700;
            font-size: 0.8rem;
        }

        .lynx-image {
            width: 100%;
            object-fit: contain;
            border-radius: 7px;
            border: 1px solid rgba(23, 32, 26, 0.12);
            background: #f3efe4;
            display: block;
        }

        .missing-image {
            border: 1px dashed rgba(23, 32, 26, 0.28);
            border-radius: 7px;
            background: #f8f5ed;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 0.35rem;
            color: var(--muted);
            text-align: center;
            padding: 1rem;
        }

        .match-row {
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 1rem;
            background: #fffdf8;
            margin-bottom: 1rem;
        }

        .result-good {
            color: #1b7f4c;
            font-weight: 700;
        }

        .result-miss {
            color: #a54d2e;
            font-weight: 700;
        }

        .scorebar {
            background: rgba(23, 32, 26, 0.08);
            height: 0.65rem;
            border-radius: 999px;
            overflow: hidden;
            margin: 0.2rem 0 0.7rem;
        }

        .scorebar span {
            display: block;
            height: 100%;
            background: linear-gradient(90deg, var(--leaf), var(--sun));
            border-radius: 999px;
        }

        .chip {
            display: inline-block;
            border: 1px solid rgba(45, 106, 79, 0.28);
            border-radius: 999px;
            padding: 0.18rem 0.55rem;
            margin: 0 0.3rem 0.35rem 0;
            color: #244f3d;
            background: rgba(218, 235, 223, 0.7);
            font-size: 0.82rem;
        }

        div[data-testid="stMetricValue"] {
            color: var(--leaf);
        }

        div[role="radiogroup"] {
            gap: 0.55rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_gallery(demo: dict) -> None:
    st.subheader("Reference lynx")
    cols = st.columns(len(demo["identities"]))
    for col, identity in zip(cols, demo["identities"]):
        with col:
            st.markdown('<div class="lynx-card">', unsafe_allow_html=True)
            st.markdown(
                image_markup(identity["image"], identity["name"], max_height=240),
                unsafe_allow_html=True,
            )
            st.markdown(f"#### {identity['name']}")
            st.caption(identity.get("caption", ""))
            st.markdown("</div>", unsafe_allow_html=True)


def render_guessing(demo: dict) -> None:
    identities = demo["identities"]
    name_for_id = {identity["id"]: identity["name"] for identity in identities}
    current_queries = active_queries(demo)

    st.subheader("Student guesses")
    st.caption(
        "Each mystery photo is paired with the reference choices beside it."
    )
    for index, query in enumerate(current_queries, start=1):
        reference_identities = reference_identities_for_query(query, demo)
        options = [identity["id"] for identity in reference_identities]
        current_guess = st.session_state["guesses"].get(query["id"], options[0])
        if current_guess not in options:
            current_guess = options[0]
            st.session_state["guesses"][query["id"]] = current_guess

        st.markdown('<div class="comparison-card">', unsafe_allow_html=True)
        st.markdown(f"### {index}. {query['label']}")
        st.caption(query.get("prompt", "Choose the closest reference identity to the individual animal."))

        left, right = st.columns([0.78, 1.8], vertical_alignment="top")
        with left:
            st.markdown('<div class="mystery-panel">', unsafe_allow_html=True)
            st.markdown("**Mystery photo**")
            st.markdown(
                image_markup(query["image"], query["label"], max_height=360),
                unsafe_allow_html=True,
            )
            st.markdown(
                "<span class='chip'>spot pattern</span>"
                "<span class='chip'>ear tufts</span>"
                "<span class='chip'>tail tip</span>"
                "<span class='chip'>facial ruffs</span>"
                "<span class='chip'>dorsal ridge line</span>",
                unsafe_allow_html=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)

        with right:
            st.markdown(
                "<div style='font-size: 1.6rem; font-weight: 700; color: yellow; margin-bottom: 0.35rem;'>"
                "Choose the matching reference"
                "</div>",
                unsafe_allow_html=True,
            )

            selected = st.radio(
                "Choose the matching reference",
                options=options,
                format_func=lambda value: name_for_id[value],
                index=options.index(current_guess),
                key=f"guess_{query['id']}",
                horizontal=True,
                label_visibility="collapsed",
            )
            st.session_state["guesses"][query["id"]] = selected

            top_row = st.columns(2)
            bottom_row = st.columns(2)
            card_slots = top_row + bottom_row
            for card_col, identity in zip(card_slots, reference_identities):
                is_selected = identity["id"] == selected
                selected_class = " selected" if is_selected else ""
                selected_text = (
                    "<div class='selected-label'>Selected by class</div>"
                    if is_selected
                    else "<div class='small-note'>Reference option</div>"
                )
                with card_col:
                    st.markdown(
                        f'<div class="reference-option{selected_class}">',
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        image_markup(identity["image"], identity["name"], max_height=225),
                        unsafe_allow_html=True,
                    )
                    st.markdown(f"#### {identity['name']}")
                    st.markdown(f"<p>{identity.get('caption', '')}</p>", unsafe_allow_html=True)
                    st.markdown(selected_text, unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

            if st.session_state["revealed"]:
                correct_id = query["correct_identity"]
                if selected == correct_id:
                    st.markdown("<p class='result-good'>Class guess: correct</p>", unsafe_allow_html=True)
                else:
                    st.markdown(
                        f"<p class='result-miss'>Class guess: {name_for_id[selected]}</p>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(f"Correct identity: **{name_for_id[correct_id]}**")

        st.markdown("</div>", unsafe_allow_html=True)


def run_analysis_animation() -> None:
    steps = [
        "Locating body outline and face region",
        "Extracting coat spot constellations",
        "Comparing ear tufts and cheek ruff",
        "Compute Cosine similarity of mega-descriptors",
        "Measuring similarity against known identities",
        "Similarity threshold mapping",
        "Finalizing the Answer",
        "Double checking the patterns",
        "Looking for mistakes",
        "Checking matches",
        "Calibrating confidence scores",
        "Wait.....",
        "Just a bit",
        "It's done!!!!!",
    ]
    progress = st.progress(0, text="Preparing ReID analysis")
    status = st.empty()
    for step_number, step in enumerate(steps, start=1):
        status.info(step)
        progress.progress(step_number / len(steps), text=step)
        time.sleep(2.00)
    status.success("Identity matches ready")
    time.sleep(0.30)
    st.session_state["analysis_ran"] = True
    st.session_state["revealed"] = True


def render_reveal(demo: dict) -> None:
    by_id = identity_by_id(demo)
    current_queries = active_queries(demo)

    c1, c2, c3 = st.columns(3)
    guesses = st.session_state["guesses"]
    correct_count = sum(
        1 for query in current_queries if guesses.get(query["id"]) == query["correct_identity"]
    )
    c1.metric("Mystery Photos", len(current_queries))
    c2.metric("Audience Points out of 3", f"{correct_count}/{len(current_queries)}")
    c3.metric("AI Points out of 3", f"{len(current_queries)}/{len(current_queries)}")

    if not st.session_state["revealed"]:
        st.info("When the audience has finished guessing, please run the reveal to see the magic.")
        return

    st.subheader("AI ReID results")
    for query in current_queries:
        reference_identities = reference_identities_for_query(query, demo)
        correct = by_id[query["correct_identity"]]
        st.markdown('<div class="match-row">', unsafe_allow_html=True)
        photo_col, ref_col, score_col = st.columns([1, 1, 1.2])
        with photo_col:
            st.markdown("**Mystery photo**")
            st.markdown(
                image_markup(query["image"], query["label"], max_height=260),
                unsafe_allow_html=True,
            )
        with ref_col:
            st.markdown(f"**Matched identity: {correct['name']}**")
            st.markdown(
                image_markup(correct["image"], correct["name"], max_height=260),
                unsafe_allow_html=True,
            )
        with score_col:
            st.markdown("**Similarity ranking**")
            for identity_id, score in ranked_scores(query, reference_identities):
                name = by_id[identity_id]["name"]
                st.markdown(f"{name} - **{score}%**")
                st.markdown(
                    f'<div class="scorebar"><span style="width:{score}%"></span></div>',
                    unsafe_allow_html=True,
                )
            st.markdown("**Evidence cues**")
            for cue in query.get("evidence", []):
                st.markdown(f"<span class='chip'>{cue}</span>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.success(
        "Presenter note: this demo uses pre-identified results from an AI model. "
        "It is designed to explain how animal ReID can reduce the need for intrusive tagging which helps the animal welfare."
    )


def render_discussion(demo: dict) -> None:
    st.subheader("Discussion prompts")
    for prompt in demo.get("discussion_prompts", []):
        st.markdown(f"- {prompt}")

    st.subheader("Key message")
    st.markdown(
        "AI ReID systems compare natural markings that animals already have. "
        "For species like lynx, this can help researchers monitor individuals with camera-trap photos, "
        "while reducing stressful capture or tagging in some study designs. It also saves time for the conservationists, but it is still just a tool."
        "A knife for example can be used for a sugery to save someone or to hurt someone. Same with the AI, if poachers get it then they can use it too to harm animals instead of protecting them."
        
    )


def main() -> None:
    demo = load_demo()
    initialize_state(demo)
    render_css()

    st.markdown('<section class="hero">', unsafe_allow_html=True)
    
   
    title_col, logo_col = st.columns([4, 1], vertical_alignment="center")
    
    with title_col:
        st.title(demo.get("title", "Individual Lynx Recognition"))
        
    with logo_col:
        
        st.image("assets/logo.png", width="stretch")

    st.markdown(f"### {demo.get('subtitle', '')}")
    st.markdown(f"#### *{demo.get('subsubtitle', '')}*")
    st.markdown(demo.get("intro", ""))
    st.markdown("</section>", unsafe_allow_html=True)

    with st.sidebar:
        st.header("Presenter controls")
        if st.button("Run AI ReID reveal", type="primary", use_container_width=True):
            run_analysis_animation()
            st.rerun()
        if st.button("New random round", use_container_width=True):
            reset_demo(demo)
            st.rerun()

        st.divider()
        st.markdown("**Demo setup**")
        st.caption(f"Manifest: `{DATA_FILE.relative_to(ROOT)}`")
        st.caption("Insert CzechLynx photos and update the manifest.")

        with st.expander("Project transparency note:"):
            st.write(
                "The reveal is pre-identified by AI model before the demo. It serves to demonstrate the concept of individual animal identification, a crucial part of this world of tagging."
            )

    guess_tab, reveal_tab, discussion_tab = st.tabs(
        ["1. Game Guess!", "2. AI Reveal's the Answer!", "3. Discussion Part!"]
    )
    with guess_tab:
        render_guessing(demo)
    with reveal_tab:
        render_reveal(demo)
    with discussion_tab:
        render_discussion(demo)

if __name__ == "__main__":
    main()
