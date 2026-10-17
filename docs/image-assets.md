# Project imagery

All four assets were generated using the **built-in image_gen tool**, then encoded as JPEGs for the website. PNG masters are in `output/imagegen/`. No external stock images or remote hotlinks are required. These are illustrations of the project context, not evidence of deployed AGECM hardware. Page captions/footer disclose AI imagery.

| Website asset | Where used | Prompt brief |
|---|---|---|
| `frontend/public/images/mine-workers.jpg` | Homepage hero | Photorealistic documentary photograph of a spacious supported underground hard-rock mine. Three mine workers in helmets, lamps, safety glasses and orange reflective PPE inspect a wall-mounted measurement point and record observations on a tablet. Wide 2.3:1 environmental framing, workers left, darker space right for page copy; charcoal rock, practical lighting. No logos, text, watermarks or fictional overlays. |
| `frontend/public/images/field-sensing.jpg` | Sensing capability, monitoring and alert headers, hardware overview | Industrial editorial photograph of a gloved mine technician inspecting a rugged tilt/distance monitoring housing fixed to rough rock, with a separate fixed reference target and neat cabling. Natural rock and metal textures, orange PPE, 4:3 crop, no readable markings, text, logos or holograms. |
| `frontend/public/images/laboratory-rig.jpg` | Movement analysis, analytics header, project vision | University laboratory bench with two ESP32 development boards and small sensor breakouts on a wired tilt rig, a separate fixed ToF target and student hands adjusting the rig. Soft background laptop with indistinct line plots. Cool gray surfaces, restrained orange detail, natural editorial photography, landscape 4:3, no readable data or branding. |
| `frontend/public/images/central-display.jpg` | Cloud capability, architecture header, central hardware | Compact unbranded ESP32 wired to a small LCD module on a university lab bench, USB lead, tidy jumper wires and screwdriver. Exactly one microcontroller and one display, no sensing role; screen contains no legible invented data. Blurred rock samples, charcoal workbench, soft warm light, 4:3 framing, no logos or overlays. |

The field image illustrates the eventual monitoring context; it does not imply that an ESP32 has been installed in a real mine. The lab/display images are concept imagery rather than exact PCB, firmware, wiring or product documentation. Actual wiring is documented separately.

Image containers retain an intentional background and accessible alt text. If an asset fails to load, a project label and the container geometry remain, preserving the layout. Images below the hero load lazily; website JPEGs total approximately 1.7 MB. Original full-resolution masters remain available for future edits.
