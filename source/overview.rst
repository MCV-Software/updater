Overview
===================

The updater package is intended to help provide automatic updates to users of applications on various operating systems (currently Microsoft Windows, GNU/Linux and MacOS X). By reading a json file, which should be available over internet and contains information about the latest version of the application, as well as links to distributable versions, This package can display a notification about new versions of the software, download and install it automatically. On windows, the bootstrapper module -which handles the update installation process, will request for elevated privileges in order to copy files to the application folder.

Requirements
----------

In order to provide with automatic updates to everyone, you need to satisfy the following requirements:

* Your python application must already be distributable (frozen or built with the tool of your choice).
* Your distributable application must bundle one of the available bootstrappers, present in the updater package. Currently, we do have bootstrappers for Windows, Linux and MacOS x. The bootstrapper file must be present in the root folder of the distributable application.
* You need to create a json file with information about your application. You can include fields such as the latest version, a brief list of changes, and download links to zip files, containing your distributable application. Those zip files might be available for different operating systems and architectures, if you distribute for different systems. Optionally, those zip files can be password protected, and you can pass the password in the instantiation of the updater package.
* You need to instantiate one of the available updater modules (currently, the only available module is WxUpdater) and pass the URL of your json file, as well as your application's current version and name. Optionally, you can customize the messages users will see when there are updates available, when updates are downloading or when the update is about to be installed. Once instantiated, just call check_for_updates() in the class, and the process will begin. If there are no updates available, or there are no updates for the user's architecture, nothing will happen. If there is a new valid update, the user will be prompted to download it. If he/she accepts, the update will be downloaded and installed.