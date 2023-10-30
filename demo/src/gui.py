import os

import gradio as gr

from .inference import run_model
from .logger import setup_logger, read_logs
from .utils import load_ct_to_numpy
from .utils import load_pred_volume_to_numpy
from .utils import nifti_to_glb


# setup logging
LOGGER = setup_logger()


class WebUI:
    def __init__(
        self,
        model_name: str = None,
        cwd: str = "/home/user/app/",
        share: int = 1,
    ):
        # global states
        self.images = []
        self.pred_images = []

        # @TODO: This should be dynamically set based on chosen volume size
        self.nb_slider_items = 820

        self.model_name = model_name
        self.cwd = cwd
        self.share = share

        self.class_name = "airways"  # default
        self.class_names = {
            "airways": "CT_Airways",
            "lungs": "CT_Lungs",
        }

        self.result_names = {
            "airways": "Airways",
            "lungs": "Lungs",
        }

        # define widgets not to be rendered immediantly, but later on
        self.slider = gr.Slider(
            minimum=1,
            maximum=self.nb_slider_items,
            value=1,
            step=1,
            label="Which 2D slice to show",
        )
        self.volume_renderer = gr.Model3D(
            clear_color=[0.0, 0.0, 0.0, 0.0],
            label="3D Model",
            visible=True,
            elem_id="model-3d",
        ).style(height=512)

    def set_class_name(self, value):
        print("Changed task to:", value)
        self.class_name = value

    def combine_ct_and_seg(self, img, pred):
        return (img, [(pred, self.class_name)])

    def upload_file(self, file):
        return file.name

    def process(self, mesh_file_name):
        path = mesh_file_name.name
        run_model(
            path,
            model_path=os.path.join(self.cwd, "resources/models/"),
            task=self.class_names[self.class_name],
            name=self.result_names[self.class_name],
        )
        nifti_to_glb("prediction.nii.gz")

        self.images = load_ct_to_numpy(path)
        self.pred_images = load_pred_volume_to_numpy("./prediction.nii.gz")

        return "./prediction.obj"

    def get_img_pred_pair(self, k):
        k = int(k)
        out = gr.AnnotatedImage(
            self.combine_ct_and_seg(self.images[k], self.pred_images[k]),
            visible=True,
            elem_id="model-2d",
        ).style(
            color_map={self.class_name: "#ffae00"},
            height=512,
            width=512,
        )
        return out

    def run(self):
        css = """
        #model-3d {
        height: 512px;
        }
        #model-2d {
        height: 512px;
        margin: auto;
        }
        #upload {
        height: 120px;
        }
        .logs {
        width: 120px;
        margin: auto;
        }
        """
        with gr.Blocks(css=css) as demo:
            with gr.Row():
                with gr.Column():
                    with gr.Row():
                        file_output = gr.File(file_count="single", elem_id="upload")
                        file_output.upload(self.upload_file, file_output, file_output)

                        model_selector = gr.Dropdown(
                            list(self.class_names.keys()),
                            label="Task",
                            info="Which task to perform",
                            multiselect=False,
                            size="sm",
                        )
                        model_selector.input(
                            fn=lambda x: self.set_class_name(x),
                            inputs=model_selector,
                            outputs=None,
                        )

                        run_btn = gr.Button("Run analysis").style(
                            full_width=False, size="lg"
                        )
                        run_btn.click(
                            fn=lambda x: self.process(x),
                            inputs=file_output,
                            outputs=self.volume_renderer,
                        )

                    with gr.Row():
                        gr.Examples(
                            examples=[
                                os.path.join(self.cwd, "test_thorax_CT.nii.gz"),
                            ],
                            inputs=file_output,
                            outputs=file_output,
                            fn=self.upload_file,
                            cache_examples=True,
                        )

                    with gr.Row():
                        with gr.Box():
                            with gr.Column():
                                # create dummy image to be replaced by loaded images
                                t = gr.AnnotatedImage(
                                    visible=True, elem_id="model-2d"
                                ).style(
                                    color_map={self.class_name: "#ffae00"},
                                    height=512,
                                    width=512,
                                )

                                self.slider.input(
                                    self.get_img_pred_pair,
                                    self.slider,
                                    t,
                                )

                                self.slider.render()

                        with gr.Box():
                            self.volume_renderer.render()
                
                with gr.Column(visible=True, style="logs", scale=0.2) as sidebar_left:
                    gr.Markdown("SideBar Right")

                    logs = gr.Textbox(label="Logs", info="Verbose from inference will be displayed below.", max_lines=16, autoscroll=True, elem_id="logs")
                    demo.load(read_logs, None, logs, every=1)

        # sharing app publicly -> share=True:
        # https://gradio.app/sharing-your-app/
        # inference times > 60 seconds -> need queue():
        # https://github.com/tloen/alpaca-lora/issues/60#issuecomment-1510006062
        demo.queue().launch(
            server_name="0.0.0.0", server_port=7860, share=self.share
        )
