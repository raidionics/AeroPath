import os

import gradio as gr
from zipfile import ZipFile
from PIL import Image

from .convert import nifti_to_obj
from .css_style import css
from .inference import run_model
from .logger import flush_logs
from .logger import read_logs
from .logger import setup_logger
from .utils import load_ct_to_numpy
from .utils import load_pred_volume_to_numpy

# setup logging
LOGGER = setup_logger()


class WebUI:
    def __init__(
        self,
        model_name: str = None,
        cwd: str = "/home/user/app/",
        share: int = 1,
    ):
        self.file_output = None
        self.model_selector = None
        self.stripped_cb = None
        self.registered_cb = None
        self.run_btn = None
        self.slider = None
        self.download_file = None

        # global states
        self.images = []
        self.pred_images = []

        self.model_name = model_name
        self.cwd = cwd
        self.share = share

        self.class_name = "Airways"  # default
        self.class_names = {
            "Airways": "CT_Airways",
        }

        self.result_names = {
            "Airways": "Airways",
        }

        self.volume_renderer = gr.Model3D(
            clear_color=[0.0, 0.0, 0.0, 0.0],
            label="3D Model",
            visible=True,
            elem_id="model-3d",
            height=512,
        )
        # self.volume_renderer = ShinyModel3D()

    def set_class_name(self, value):
        LOGGER.info(f"Changed task to: {value}")
        self.class_name = value

    def combine_ct_and_seg(self, img, pred):
        return (img, [(pred, self.class_name)])

    def upload_file(self, file):
        out = file.name
        LOGGER.info(f"File uploaded: {out}")
        return out

    def process(self, mesh_file_name):
        path = mesh_file_name.name
        run_model(
            path,
            model_path=os.path.join(self.cwd, "resources/models/"),
            task=self.class_names[self.class_name],
            name=self.result_names[self.class_name],
        )
        LOGGER.info("Converting prediction NIfTI to OBJ...")
        nifti_to_obj("prediction.nii.gz")

        LOGGER.info("Loading CT to numpy...")
        self.images = load_ct_to_numpy(path)

        LOGGER.info("Loading prediction volume to numpy..")
        self.pred_images = load_pred_volume_to_numpy("./prediction.nii.gz")

        slider = gr.Slider(
            minimum=0,
            maximum=len(self.images) - 1,
            value=int(len(self.images) / 2),
            step=1,
            label="Which 2D slice to show",
            interactive=True,
        )

        return "./prediction.obj", slider

    def get_img_pred_pair(self, k):
        img = self.images[k]
        img_pil = Image.fromarray(img)
        seg_list = []
        seg_list.append((self.pred_images[k], self.class_name))
        return img_pil, seg_list

    def toggle_sidebar(self, state):
        state = not state
        return gr.update(visible=state), state

    def package_results(self):
        """Generates text files and zips them."""
        output_dir = "temp_output"
        os.makedirs(output_dir, exist_ok=True)

        zip_filename = os.path.join(output_dir, "generated_files.zip")
        with ZipFile(zip_filename, 'w') as zf:
            zf.write("./prediction.nii.gz")

        return zip_filename

    def setup_interface_outputs(self):
        with gr.Row():
            with gr.Group():
                with gr.Column(scale=2):
                    t = gr.AnnotatedImage(
                        visible=True,
                        elem_id="model-2d",
                        color_map={self.class_name: "#ffae00"},
                        height=512,
                        width=512,
                    )

                    self.slider = gr.Slider(
                        minimum=0,
                        maximum=1,
                        value=0,
                        step=1,
                        label="Which 2D slice to show",
                        interactive=True,
                    )

                    self.slider.change(fn=self.get_img_pred_pair, inputs=self.slider, outputs=t)

            with gr.Group():
                self.volume_renderer.render()
                self.download_btn = gr.DownloadButton(label="Download results", visible=False)
                self.download_file = gr.File(label="Download Zip", interactive=True, visible=False)


    def run(self):
        with gr.Blocks(css=css) as demo:
            with gr.Row():
                with gr.Column(scale=1, visible=True) as sidebar_left:
                    logs = gr.Textbox(
                        placeholder="\n" * 16,
                        label="Logs",
                        info="Verbose from inference will be displayed below.",
                        lines=38,
                        max_lines=38,
                        autoscroll=True,
                        elem_id="logs",
                        show_copy_button=True,
                        # scroll_to_output=False,
                        container=True,
                        # line_breaks=True,
                    )
                    timer = gr.Timer(value=1, active=True)
                    timer.tick(fn=read_logs, inputs=None, outputs=logs)
                    # demo.load(read_logs, None, logs, every=0.5)

                with gr.Column(scale=2):
                    with gr.Row():
                        with gr.Column(min_width=150):
                            sidebar_state = gr.State(True)

                            btn_toggle_sidebar = gr.Button(
                                "Toggle Sidebar",
                                elem_id="toggle-button",
                            )
                            btn_toggle_sidebar.click(
                                self.toggle_sidebar,
                                [sidebar_state],
                                [sidebar_left, sidebar_state],
                            )

                            btn_clear_logs = gr.Button("Clear logs", elem_id="logs-button")
                            btn_clear_logs.click(flush_logs, [], [])

                        self.file_output = gr.File(file_count="single", elem_id="upload")

                        self.model_selector = gr.Dropdown(
                            list(self.class_names.keys()),
                            label="Task",
                            info="Which structure to segment.",
                            multiselect=False,
                        )

                        with gr.Column(min_width=150):
                            self.run_btn = gr.Button("Run segmentation", variant="primary", elem_id="run-button")

                    with gr.Row():
                        gr.Examples(
                            examples=[
                                os.path.join(self.cwd, "test_thorax_CT.nii.gz"),
                            ],
                            inputs=self.file_output,
                            outputs=self.file_output,
                            fn=self.upload_file,
                            cache_examples=False,
                        )

                        gr.Markdown(
                            """
                            **NOTE:** Inference might take several minutes (Airways: ~8 minutes), see logs to the left. \\
                            The segmentation will be available in the 2D and 3D viewers below when finished.
                            """
                        )

                    self.setup_interface_outputs()

            # Define the signals/slots
            self.file_output.upload(self.upload_file, self.file_output, self.file_output)
            self.model_selector.input(fn=lambda x: self.set_class_name(x), inputs=self.model_selector, outputs=None)
            self.run_btn.click(fn=self.process, inputs=[self.file_output],
                               outputs=[self.volume_renderer, self.slider]).then(fn=lambda:
            gr.DownloadButton(visible=True), inputs=None, outputs=self.download_btn)
            self.download_btn.click(fn=self.package_results, inputs=[], outputs=self.download_file).then(fn=lambda
                file_path: gr.File(label="Download Zip", visible=True, value=file_path), inputs=self.download_file,
                                    outputs=self.download_file)
        # sharing app publicly -> share=True:
        # https://gradio.app/sharing-your-app/
        # inference times > 60 seconds -> need queue():
        # https://github.com/tloen/alpaca-lora/issues/60#issuecomment-1510006062
        demo.queue().launch(server_name="0.0.0.0", server_port=7860, share=self.share)
