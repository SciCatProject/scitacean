# Model Generator

This directory contains the code to generate Python classes for all relevant SciCat models.
Specifically, Pydantic models for upload and download, dataclasses for user-facing models, and the base class for `Dataset`.

First, schemas are extracted from a running SciCat instance.
Then, the upload and download models are merged into 'specs'.
The specs are extended and modified based on the YAML files in the `spec` directory.
(See the comments in those files for explanations.)
Finally, Python code is generated by rendering the jinja2 templates in the `templates` directory.

## Running

### Set up

The schemas are not exposed on production instances of SciCat.
So you need to launch one locally.
For this, clone the backend repo or download the source code for a release from https://github.com/SciCatProject/scicat-backend-next.

In this repository, launch a docker container and build SciCat as described in their README or by following these steps:

Launch container:
```shell
docker compose -f ./docker-compose.dev.yaml up
```

Find container hash:
```shell
docker container ls
```

Build and start SciCat:
```shell
docker exec <container-hash> npm run start:dev
```

Now, the schemas should be accessible under http://localhost:3000/explorer-json
The port may vary if the configuration in docker-compose.dev.yaml changes.

### Run the generator

In the same directory as this README:
```shell
python generate_models.py
```

This overwrites the relevant files in the source directory.

See `generate_models.py` for options to configure the schema URL and output file paths.