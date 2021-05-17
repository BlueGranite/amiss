
# Comparison of missing data handling methods in building variant pathogenicity metapredictors

## Description

This project will compare methods for handling missing data in variant annotations for the purpose of building variant pathogenicity metapredictors.

See [the research plan](docs/research_plan/research_plan.md) for a more detailed description. 

To generate a PDF version with a working references section:

```
$ git clone https://github.com/blueprint-genetics/amiss.git
$ cd amiss/docs/research_plan
$ make
```

[Pandoc](https://pandoc.org/) and a [LaTeX distribution](https://www.latex-project.org/) must be installed.

## Open science

This project conforms to the principles of open science:

- Open data:
  - We use and reference publically available datasets and will citably archive any data and code we produce using [Zenodo](https://zenodo.org/) with a DOI
- Open source:
  - The source code is freely available under the [MIT license](https://github.com/blueprint-genetics/amiss/blob/master/LICENSE) at [GitHub](https://github.com/blueprint-genetics/amiss)
- Open notebook:
  - You can follow development from the start on GitHub at https://github.com/blueprint-genetics/amiss
  - The research plan is available [in the GitHub repository](https://github.com/blueprint-genetics/amiss/blob/master/docs/research_plan/research_plan.md) (see [section above](#description) for producing a PDF version)
- Open access:
  - We will upload a preprint of the resulting paper(s) on [biorXiv](https://www.biorxiv.org/)
  - We will submit the results for publication in a peer-reviewed open access journal
- Open communication:
  - We intend to present the results in public scientific conferences
- Open collaboration:
  - We welcome
    - [ideas, bug reports and comments](https://github.com/blueprint-genetics/amiss/issues)
    - [code contributions through GitHub pull requests](https://github.com/blueprint-genetics/amiss/pulls)

## Running in Docker

1. Open terminal and navigate to the directory of this repository.

2. Run the following command, which will generate the Docker image.
```sh
docker build -t bgamiss .
```

3. Once the image has been created successfully, run the container locally using the following command.
```sh
docker run -p 8080:80 --name bgamiss -it bgamiss
```

Note: You will need to change the `"authLevel": "function"` setting in the _functions.json_ file to `"authLevel": "anonymous"` to test the API in the Docker container locally.

To browse the Docker container, run the following:
```sh
docker exec -it bgamiss /bin/sh
```
