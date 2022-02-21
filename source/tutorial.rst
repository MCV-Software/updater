Tutorial
===================

this is a brief tutorial that will help you to implement automatic updates within your Python application. At the end of this tutorial, you should have done a working implementation of app updates. The only prerequisite is to have a working application which uses already wx python, and is already distributable (for example, built with Nuitka, Py2exe or similar).

1. Preparing your app
---------------------

The first step in order to implement updates within your application, is to prepare the app to handle it. Here we assume you have a working application, which is already able to be packaged via your tool of choice (such as CX-Freeze, nuitka, Py2exe, etc.). You need to import the updater module from within your application, and define some important data, such as the update URL (the URL where the updater will connect to retrieve update information). You normally will implement update checking functionality during application startup, and it might look like the following code::

    from updater.wxupdater import WXUpdater

    # here we assume your app current version is 1.0, and your json file is at
    # https://example.com/update.json.
    # Of course, replace the link for the one you will provide.
    updater = WXUpdater(app_name="My awesome app", current_version="1.0", endpoint="https://example.com/update.json")
    # by calling check_for_updates, the process will start and user will be notified if there is any.
    updater.check_for_updates()

:note: 
    The update process will compare if the string passed as current_version is the same in the update json file. So in order to create an update, you just will need to provide the update file with a different current version. Obviously, every time you update the app, you need to update the current_version.

After implemented this within your application, you can safely prepare a distributable version as you prefer in order to be ready for the next step.

2. Bundle bootstrapper.
------------------------------

In order for your applications to be updated, you need to bundle the correct bootstrapper module within your application distribution folder. The bootstrapper module is responsible for copying the updates to the original application folder, and restart the app process when finished. There is a bootstrapper for every platform supported. If you want to take a look to the source code of those bootstrapper files, you can see the `Updater's repository <https://github.com/mcv-software/updater>`_ and take a look there.

By default, bootstrappers for all platforms are available in Python's site packages directory, inside the updater package folder, in a directory called bootstrappers. There, you'll have 4 files: bootstrapper.exe (for Windows, already built), bootstrapper.pb (for Windows, source code), bootstrapper-lin.sh (for GNU/Linux) and bootstrapper-mac.sh (for OS X). Pic the one you need from there and place it inside your distribution folder.

:note:
    Pay special attention to the location of the bootstrapper file within your application folder. The bootstrapper must be in the root directory of the application. Any other location will make the update process to fail.

3. Creating the update file
---------------------------

Once you have your distribution folder alongside with the bootstrapper for your platform, it's time to generate the update file. The update file is basically a zipfile which contains your application folder.

:note:
    Please take into account that the updater package uses the Python's standard library :py:class:`zipfile.ZipFile` class to unzip the update file. Please don't compress the update file unnecesarily or use another format.

:note:
    You need to create the update file from within the distribution folder. That means that the application files must be in the root of the zip file.

Once your zip file is ready, upload it in a server which offers a direct link. Please avoid any public cloud (such as google Drive and similar) as public links are not easy to follow from there. For this tutorial, we will assume the file has been uploaded to https://example.com/updatefile.zip.

4. Generate the update information file
---------------------------------------

Once you have uploaded your update file, it's time to create a json file, which will contain information about your latest version, as well as any download link you want to provide. For this tutorial's purposes, we will offer only a Windows download, for 64 bits architecture. You can define your downloads section based in the architectures and platforms you support. The information in the json file should look like this::

    {"current_version": "2.0",
    "description": "Changed version from 1 to 2.0.",
    "downloads":
        {"Windows64": "https://example.com/updatefile.zip"
    }

Take into account that downloads should be added by aggregating data about operating system and architecture. Basically we take the return value of :py:func:`platform.system`, plus the first two digits on the first item in the tuple returned by :py:func:`platform.architecture` to look for architecture files. For example, those are valid architecture files for the currently supported operating systems:

* Windows32
* Windows64
* Linux32
* Linux64
* Darwin64

:note:
    Pay attention to capitalization when defining downloads, as the updater might fail if capitalization is not done properly. Remember that the download architecture should be the result of `platform.system()+platform.architecture()[0][:2]` in all cases.

:note:
    A Malformed json file will cause the updater instance to fail when checking for an update. If you want to be sure your json is valid, you can use an `Online validator <https://jsonlint.com>`_

Once your json file is ready, please put it somewhere accessible over the internet. For the purposes in this tutorial, as we already defined before, let's assume we upload the file at https://example.com/update.json

5. Conclusion
----------------

If you have followed this tutorial until here, you should have implemented the update functionality withing your Python application. In order for testing the update feature, you just need to launch the event where you have implemented the updater. You should see an update available message dialog and the options to accept to download it or cancel the action.

A side effect of the current implementation we have done in this tutorial, is that every time you launch the updater, it will inform you about a new update. In order to avoid this, remember that the current version in both sides (the application and the update json file) must match.

Finally, you can customize all messages that the updater displays to users via some optional variables that can be passed to the updater constructor. For more information, please read the :py:class:`updater.wxupdater.WXUpdater` module for more information.