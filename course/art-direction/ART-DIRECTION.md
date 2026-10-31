# Becoming Doom: art direction v1 (for approval)

The visual sheet is `course/video/film/art-direction.html`, which renders to
`/mnt/project-files/course/art-direction/Becoming-Doom-Art-Direction-v1.pdf`.

## The law
1. Most of every frame is pure black, with around 70% below visible detail.
2. One hard light source, from the side or as a rim light. It lights the face, the hands and the object, and nothing else.
3. Red is the only colour, with at most one red accent per frame. No blue, no teal, no warm beige.
4. Black on black: fabric, stone, wet floor, matte metal.

## Grade
Every image goes through `python3 tools/doom_grade.py in.png out.png` after generation. The grade:
- strips cool hues back to 18%
- protects red and skin tones
- crushes the black point
- applies an S curve with a low pivot
- adds a vignette into black and fine grain

## Palette
| Name | Hex |
|---|---|
| Void | #000000 |
| Pitch | #0B0B0C |
| Iron | #141416 |
| Ash | #2A2A2E |
| Steel | #7C7C80 |
| Mist | #B4B4B8 |
| Bone | #EDEDED |
| Blood | #7A0606 |
| Doom Red (the only accent) | #D90D0D |

All greys are neutral. The warm ivory and stone tones have been retired.

## Type
Anton is for headlines, always in caps, ending on a red full stop or a red key word.
Inter Tight is for everything else, including the wide-tracked poster lines. There is no third font.

## GPT Image 2.5 recipe
[Subject and action], [setting], at night. Low-key cinematic photograph. A single hard side light from [left or right] catches the face and hands; everything else falls into deep, pure black shadow. Around 70% of the frame is near black. One small practical red light source, [e.g. a thin red strip light], as the only colour. Black on black wardrobe and surfaces, matte and wet textures. Neutral, desaturated tones with no blue or teal cast, no warm beige. No daylight, no dusk sky, no bright windows. Shot on a 35mm or 50mm lens, shallow depth of field, fine film grain, high contrast, crushed blacks. Photorealistic, 16:9. No text, no logos, no watermarks.

Generate at 3840x2160 and run the grade. If the eyes no longer read, regenerate rather than brightening.
