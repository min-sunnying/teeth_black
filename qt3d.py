import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from PyQt5.QtGui import QImage, QPixmap

class Show3d:
    def __init__(self):
        pass

    # draw 3d plot
    def show3d(self):
        fig = plt.figure()
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(projection="3d")
        x=[]
        y=[]
        z=[]
        for idx1, e1 in enumerate(self.save_croped):
            for idx2, e2 in enumerate(e1):
                for idx3, e3 in enumerate(e2):
                    if e3==0:
                        x.append(idx2)
                        y.append(idx3)
                        z.append(-self.gap.value()*int(self.crop_image[idx1][0][0:5]))
        ax.scatter(x,y,z, marker='o', s=15, c='darkgreen', alpha=.25)
        ax.axis('off')
        canvas.draw()
        width, height = fig.figbbox.width, fig.figbbox.height
        img = QImage(canvas.buffer_rgba(), width, height, QImage.Format_ARGB32)
        pixmap = QPixmap(img)
        self.image3d.setPixmap(pixmap)
        # ratio button enable
        self.ratio.setEnabled(True)
        self.progress6()
        self.resizeimage()
        plt.close(fig)