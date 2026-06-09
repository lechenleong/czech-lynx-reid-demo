# CzechLynx ReID Demo

This is a Streamlit demo for an elementary-school activity about individual animal ReID. Students first match mystery lynx photos by eye, then the simulated "AI" reveal shows predefined answers with confidence-style scoring.

![lyxn annotation](web_media/lynx_data_keypoints.png)


## Run

```powershell
pip install -r requirements.txt
streamlit run app.py
```

## Customize the lynx IDs

Edit `data/lynx_demo.json`.

- Add each known individual under `identities`.
- Add each classroom mystery photo under `queries`.
- Set `correct_identity` to one of the identity IDs.
- Put your image files in `assets/` or use any path relative to this folder.
- The app randomly picks 3 mystery photos for each round.
- Each mystery photo gets 4 reference choices: the correct identity plus 3 distractors.
- Optional: add `reference_choices` to a query if you want to control which identities can appear as choices for that photo.

Example:

```json
{
  "id": "mystery_01",
  "label": "Mystery photo 1",
  "image": "assets/czechlynx/mystery_01.jpg",
  "correct_identity": "lynx_mira",
  "confidence": 97,
  "reference_choices": ["lynx_kora", "lynx_mira", "lynx_sava", "lynx_tibor"],
  "evidence": ["shoulder spots", "cheek stripe", "flank pattern"]
}
```

Click **New random round** in the sidebar to sample another set of 3 mystery photos.

