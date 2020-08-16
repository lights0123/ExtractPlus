# ExtractPlus

A program to extract MotoPlus header files from publicly available documentation PDFs

## Introduction

The Yaskawa MotoPlus SDK is the official toolchain for writing C programs. However, it comes with a
few problems:

- Only Windows with Visual Studio is supported
- A license is potentially expensive
- An old GCC is used, with only support for the C language
- A Sentinel USB DRM key is required to be plugged in while using the software. You need to install
  their Windows drivers, and if you lose the key, you have to buy another one.

There's truly nothing special about the SDK—all Motoman controllers except the FS100 (which is
PowerPC) are just Intel x86/i386 boards running VxWorks. Helpfully, the C ABI on VxWorks and Linux
is... _the same_. That means that as long as we don't make Linux syscalls or link to Linux standard
libraries, we can just use stock GCC. Buying the SDK includes just a few things:

- A proprietary VGA cable
- A Visual Studio plugin
- A rebranded GCC
- Sample programs
- **The MotoPlus header files**

We don't really need the Visual Studio plugin, as you can just use any build system. We don't need
their rebranded GCC as you can just use a stock one. The only thing that we _actually_ need is the
header files. The MotoPlus SDK documentation happens to have full declarations for (almost) every
struct and function. And, helpfully, Yaskawa provides [free downloads of all of their
manuals][product documentation]! The following license is attached with them:

> These manuals are freely available as a service to Yaskawa customers to assist in the operation of
> Motoman robots, related equipment and software. These manuals are copyrighted property of Yaskawa
> and may not be sold or redistributed in any way. You are welcome to copy these documents to your
> computer or mobile device for easy access but you may not copy the PDF files to another website,
> blog, cloud storage site or any other means of storing or distributing online content.

As we cannot "redistribute" them (and likely, the generated header files), this project instead
provides a simple Python script to take those existing PDFs, extract the relevant code, and write it
out into a new header file.

[product documentation]: https://www.motoman.com/en-us/service-training/product-documentation

## Downsides

Why not use this project?

- **No support**. You're on your own if something bad happens while using this.
- Limited supported controllers. Although the documentation is available for all controllers, I
  don't have a need for controllers other than the YRC1000.
- Limited symbols. Although I generally have all functions and structs, many enums are not clearly
  stated in the manual in a machine-readable fashion. As such, I only defined the ones I needed to
  compile MotoROS.
- Lack of tools provided with the VS plugin. For example:
  - Easy project creation templates
  - Network upload of binaries to the controller
  - Debugging tools
  - Copy protection wizard

## Getting started

Start by installing dependencies. Install the python dependencies with:

```bash
pip3 install --user -r requirements.txt
```

You'll also need `pdftohtml`. This is typically provided by a package called `poppler` (Arch Linux)
or `poppler-utils` (Ubuntu).

Currently, the YRC1000 and YRC1000micro are the only controllers that can be fully extracted. This
depends on [the YRC1000 MotoPlus API documentation][yrc1000 motoplus]. This is titled "MotoPlus, New
Language Environment, API Function Specifications", with product code 178941-1CD (HW1483602). It
will be automatically downloaded by running:

```bash
wget https://www.motoman.com/getmedia/76A4DFF5-8DDF-48C2-A505-DD6B4773E17A/178941-1CD.pdf.aspx -O 178941-1CD.pdf
pdftohtml -i -noframes 178941-1CD.pdf YRC1000.html
./main.py YRC1000.html > MotoPlus.h
```

A sample Makefile is present that is designed for working with MotoROS. Copy it and MotoPlus.h to
your source directory, or change the `SRC` variable to point to the directory. Then, just run
`make`.

[yrc1000 motoplus]:
  https://www.motoman.com/getmedia/76A4DFF5-8DDF-48C2-A505-DD6B4773E17A/178941-1CD.pdf.aspx

# Disclaimer

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR
IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

I am not responsible if something bad happens to your robot as a result of using this software.
