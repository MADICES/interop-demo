IDS = {
    "@aiida.Simulation": {
        "prefix": "SIM",
        "counter": 1,
    },
    "@aiida.Workflow": {
        "prefix": "WF",
        "counter": 1,
    },
    "@aiida.Sample": {
        "prefix": "SAMPLE",
        "counter": 2,
    },
    "@aiida.Object": {
        "prefix": "OBJ",
        "counter": 0,
    },
}

MAPPING = {
    "https://aiida.net/Simulation": "@aiida.Simulation",
    "https://aiida.net/Workflow": "@aiida.Workflow",
    "https://schema.org/Protein": "@aiida.Sample",
    "https://schema.org/MolecularEntity": "@aiida.Sample",
}

CONTEXT: dict[str, dict] = {
    "https://aiida.net/Simulation": {
        "@context": {},
    },
    "https://aiida.net/Workflow": {
        "@context": {},
    },
    "https://schema.org/Protein": {
        "@context": {},
    },
    "https://schema.org/MolecularEntity": {
        "@context": {
            "key": {
                "@id": "https://schema.org/inChIKey",
                "@type": "xsd:string",
            },
            "label": {
                "@id": "https://schema.org/iupacName",
                "@type": "xsd:string",
            },
            "formula": {
                "@id": "https://schema.org/molecularFormula",
                "@type": "xst:string",
            },
            "weight": {
                "@id": "https://schema.org/molecularWeight",
                "@type": "xsd:float",
            },
            "units": {
                "@id": "https://schema.org/molecularWeightUnits",
                "@type": "xsd:string",
            },
        },
    },
}

DATA = [
    {
        "id": "SIM-1",
        "type": "@aiida.Simulation",
        "title": "A simulation of something",
        "metadata": {
            "id": "5235211",
            "aiida_version": "2.4.3",
            "creation_parameters": {
                "entities_starting_set": {
                    "node": ["0e275ed7-c1ec-4926-b0d0-3b7cc97e9ab2"]
                },
                "include_authinfos": False,
                "include_comments": True,
            },
        },
        "ontology": "https://aiida.net/Simulation",
    },
    {
        "id": "WF-1",
        "type": "@aiida.Workflow",
        "title": "A workflow of simulations",
        "metadata": {
            "uuid": "1e673a08-a0ff-47ad-9a09-52321f6dc2dc",
            "cmdline_params": ["-i", "aiida.inp"],
        },
        "ontology": "https://aiida.net/Workflow",
    },
    {
        "id": "SAMPLE-1",
        "type": "@aiida.Sample",
        "title": "Tropomyosin",
        "metadata": {
            "hasBioPolymerSequence": "GGGTTCTCTATCTCTAAAAGGTGTCAA",
        },
        "ontology": "https://schema.org/Protein",
    },
    {
        "id": "SAMPLE-2",
        "type": "@aiida.Sample",
        "title": "A crystal",
        "metadata": {
            "key": "LFQSCWFLJHTTHZ-UHFFFAOYSA-N",
            "label": "Ethanol",
            "formula": "C2H5OH",
            "weight": 46.068,
            "units": "g/mol",
        },
        "ontology": "https://schema.org/MolecularEntity",
    },
]

PLATFORMS = {
    "openBIS": 5001,
}
