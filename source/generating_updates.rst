Generating updates
===================

The updater package will work with any module used to generate distributable files, such as `Nuitka, <https://www.nuitka.net>`_ `CX-Freeze <https://pypi.org/project/cx-Freeze/>`_ and others, as long as a valid update file is provided. A valid update file is basically a zip file containing a binary distributable version of an application, plus the bootstrap binary for the operating system. The botstrap binary, as well as any other application file, must be in the root of the zipfile.

Here is what you need to do, in order to generate an update for any operating system.

1. Create the distributable version of the application. You can use any package to do so. You should end with a folder where an executable file, as well as all of its dependencies (including package data and other application files) are included.
2. Copy the bootstrapper binary file. (more instructions here).
3. Zip the whole folder of distributable files. Take into account that you need to create a zip file where your application files must be the root folder of the zip. The updater package includes a small utility command in order to create a zip file from any created folder.
4. Upload the zip file to any known site that could give you a direct URL to the file.
5. When asked, users should be able to download and install the update.