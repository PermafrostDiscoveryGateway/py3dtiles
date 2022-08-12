=========
py3dtiles
=========

Forked from https://gitlab.com/Oslandia/py3dtiles
-------------------------------------------------

py3dtiles is a Python tool and library for manipulating `3D
Tiles <https://github.com/AnalyticalGraphicsInc/3d-tiles>`_

**CLI Features**

-  Convert pointcloud LAS and XYZ files to a 3D Tiles tileset
   (tileset.json + pnts files)
-  Merge pointcloud 3D Tiles tilesets into one tileset
-  Read pnts and b3dm files and print a summary of their contents

**API features**

-  Read/write pointcloud (pnts) and batched 3d model format

py3dtiles is distributed under the Apache 2 Licence.

Gitlab repository: https://gitlab.com/Oslandia/py3dtiles

Documentation : https://oslandia.gitlab.io/py3dtiles

--------------

Changes have been made in this fork to better support the Cesium B3DM
Batched 3D Models geometry and Feature Tables.

The `gitlab-oslandia` branch is used to pull in changes from the original
creators on GitLab. This branch should be kept up to-to-date with the `master`
GitLab branch. To pull in changes locally, first add the GitLab repo as a
remote, then pull in changes from GitLab, and finally, push them to GitHub.
From the directory that contains this repo:

```
git checkout gitlab-oslandia
git remote add gitlab https://gitlab.com/Oslandia/py3dtiles.git
git pull gitlab
git push
```

When ready to update our version:
```
git checkout main
git merge gitlab-oslandia
```

README content from the original repository is below.

--------------


.. image:: https://travis-ci.org/Oslandia/py3dtiles.svg?branch=master
    :target: https://travis-ci.org/Oslandia/py3dtiles

.. image:: https://badge.fury.io/py/py3dtiles.svg
    :target: https://badge.fury.io/py/py3dtiles

=========
py3dtiles
=========

p3dtiles is a Python tool and library for manipulating `3D Tiles`_.

.. _3D Tiles: https://github.com/AnalyticalGraphicsInc/3d-tiles

**CLI Features**

* Convert pointcloud LAS and XYZ files to a 3D Tiles tileset (tileset.json + pnts files)
* Merge pointcloud 3D Tiles tilesets into one tileset
* Read pnts and b3dm files and print a summary of their contents

**API features**

* Read/write pointcloud (pnts) and batched 3d model format

py3dtiles is distributed under the Apache 2 Licence.

GitHub repository: https://github.com/Oslandia/py3dtiles

Documentation : https://oslandia.github.io/py3dtiles
