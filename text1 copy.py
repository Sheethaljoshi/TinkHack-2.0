from diffusers import DiffusionPipeline,SanaPipeline

pipe = SanaPipeline.from_pretrained("Wan-AI/Wan2.1-T2V-14B-Diffusers")

pipe.load_lora_weights("benjamin-paine/steamboat-willie-14b")

prompt = "steamboat willie style, golden era animation, a stylish woman walks down a Tokyo street  filled with warm glowing neon and animated city signage. She wears a black leather jacket,  a long red dress, and black boots, and carries a black purse. She wears sunglasses and red lipstick.  She walks confidently and casually. The street is damp and reflective, creating a mirror effect of the colorful lights.  Many pedestrians walk about."
image = pipe(prompt).images[0]