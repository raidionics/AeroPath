# Hugging Face demo - through docker SDK

Deploying simple models in a gradio-based web interface in Hugging Face spaces is easy.
For any other custom pipeline, with various dependencies and challenging behaviour, it
might be necessary to use Docker containers instead.

For every new push to the main branch, continuous deployment to the Hugging Face
`AeroPath` space is performed through a GitHub Actions workflow.

When the space is updated, the Docker image is rebuilt/updated (caching if possible).
Then when finished, the end users can test the app as they please.

Right now, the functionality of the app is extremely limited, only offering a widget
for uploading a NIfTI file (`.nii` or `.nii.gz`) and visualizing the produced surface
of the predicted lung tumor volume when finished processing.

Analysis process can be monitored from the `Logs` tab next to the `Running` button
in the Hugging Face `AeroPath` space.

It is also possible to build the app as a docker image and deploy it. To do so follow these steps:

```
docker build -t AeroPath:latest ..
docker run -it -p 7860:7860 AeroPath:latest
```

Then open `http://localhost:7860` in your favourite internet browser to view the demo.

TODOs:
- [X] Add gallery widget to enable scrolling through 2D slices
- [X] Render segmentation for individual 2D slices as overlays
