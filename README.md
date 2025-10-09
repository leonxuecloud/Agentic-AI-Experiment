# Setup new repository
To use this template, select this repository as the template when creating a new repository.

After creating a new repository
1. run `npm init` to initialise npm.
2. Copy the scripts section of the [sample package.json](https://github.com/caseware/eks-distributor-template/blob/master/sample-package.json#L6-L9) 
to the newly generated package.json

# Modifications
The default setup should work for most applications, but some teams may want extra features like
minified files.

Building and testing is fully customisable. 

For most applications, the only step that needs to be modified is the `build` script in
[package.json](./sample-package.json). It can perform extra actions and copy different files
to the build directory.

Although it shouldn't be necessary, the [build.yml](.github/workflows/build.yml) file can be
modified if needed. The only requirement is that the workflow must upload artifact containing
`additional_release_image_instructions.dockerfile` and `deploy.env` files.



