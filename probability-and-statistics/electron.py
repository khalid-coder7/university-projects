import tkinter
from turtle import bgcolor
# from tkVideoPlayer import TkinterVideo
from PIL import Image, ImageTk

from manim import *
import math, scipy
from scipy.integrate import quad

# Define constants
hbar = 1 # Planck's constant divided by 2*pi
m = 1 # Mass of the electron
w = 1 # Angular frequency
a = math.sqrt(hbar / m * w) # Length scale
qn =0 

# Define PDF function
def pdf(x):
    n = qn
    # n: energy level (0,1,2,...)
    # x: position
    N = (
        math.sqrt(1 / (2**n * math.factorial(n))) * (1 / (math.pi * a**2)) ** 0.25
    ) # Normalization Coefficient
    hermite = scipy.special.eval_hermite(n, x / a) # Hermite polynomial
    exp = math.exp(-0.5 * (x / a) ** 2) # Exponential factor
    return (N * hermite * exp) ** 2 # returns: probability density

# Define CDF function
def cdf(x):
    pdf_n = lambda x: pdf(x)
    res, err = quad(pdf_n, -np.inf, x)
    return res

bg_color = '#0D0036'

page = tkinter.Tk()

# set window size
page.geometry("1200x750")
#set window color
page.configure(bg=bg_color, bd=15)

# Code to add widgets will go here...
page.title('Probability')

img = ImageTk.PhotoImage(Image.open("0.png"))
panel = tkinter.Label(page, image=img, border=0)
#panel.pack(expand="no")
panel.grid(row=0)





def calculate(n):

    print("n=", n)
   
    if n == '0':
        img2 = ImageTk.PhotoImage(Image.open("0.png"))
    elif n == '1':
        img2 = ImageTk.PhotoImage(Image.open("1.png"))
    elif n == '2':
        img2 = ImageTk.PhotoImage(Image.open("2.png"))
    elif n == '3':
        img2 = ImageTk.PhotoImage(Image.open("3.png"))
    elif n == '4':
        img2 = ImageTk.PhotoImage(Image.open("4.png"))
    elif n == '5':
        img2 = ImageTk.PhotoImage(Image.open("5.png"))
    elif n == '6':
        img2 = ImageTk.PhotoImage(Image.open("6.png"))

    panel.configure(image=img2)
    panel.image = img2

    global qn
    qn = int(n)
    calculatePDF()
    #calculatePDF(int(n))


def calculatePDF():
    try:
        p = cdf(float(x2.get()))-cdf(float(x1.get()))
        result["text"] = "You are correct by: "+"{0:.2f}%".format(p*100)
    except:
        print(None)

result = tkinter.Label(page, text=' '
                         ,background=bg_color,
                         font= 60,
                         fg="white")
result.grid(row=0,column=3)

selector = tkinter.Scale(page, label="n =" ,from_=0, to= 6, 
                    fg="white", #label color
                    orient="horizontal",
                    activebackground= "Blue",
                    bg = bg_color, 
                    bd = 15,
                    font=90,
                    length=500,
                    showvalue=1,
                    highlightthickness=0,
                    command= calculate)#call the function calculate every time the slider changes
#selector.pack()
selector.grid(row=1)


question = tkinter.Label(page, text='Where is my electron?'
                         ,background=bg_color,
                         font= 20,
                         fg="white")
question.grid(row=2,column=3)




x1 = tkinter.StringVar() #yet7at fyhom el values beto3 el guess
x2 = tkinter.StringVar() #lazem string variable


tkinter.Label(page, text='Between',
              background=bg_color,
              fg= 'white',
              font=12).grid(row=3,column=1)
tkinter.Label(page, text='and',
              background=bg_color,
              fg="white",
              font=12,
              ).grid(row=3,column=3)

e1 = tkinter.Entry(page, width=5,
                   textvariable = x1)

e2 = tkinter.Entry(page, width=5,
                   textvariable = x2)
e1.grid(row=3, column=2)
e2.grid(row=3, column=4)




page.mainloop()