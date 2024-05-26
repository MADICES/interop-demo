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

SAMPLE_CONTEXT = {
    "was_imported": {
        "@id": "https://schema.org/wasImported",
        "@container": "@index",
        },
    "has_children": {
        "@id": "http://schema.org/children",
        "@container": "@set",
    },
}

CONTEXT: dict[str, dict] = {
    "https://aiida.net/Simulation": {
        "@context": {
            "uuid": {
                "@id": "https://aiida.net/uuid",
                "@type": "xsd:string",
            },
            "aiida_version": {
                "@id": "https://aiida.net/aiida_version",
                "@type": "xsd:string",
            },
            "creation_parameters": {
                "@id": "https://aiida.net/creation_parameters",
                "@type": "xsd:string",
            },
            "has_parent": "https://aiida.net/hasParent",
        },
    },
    "https://aiida.net/Workflow": {
        "@context": {
            "uuid": {
                "@id": "https://aiida.net/uuid",
                "@type": "xsd:string",
            },
            "cmdline_params": {
                "@id": "https://aiida.net/cmdline_params",
                "@type": "xsd:string",
            },
        },
    },
    "https://schema.org/Protein": {
        "@context": {
            **SAMPLE_CONTEXT,
            "hasBioPolymerSequence": {
                "@id": "https://schema.org/hasBioPolymerSequence",
                "@type": "xsd:string",
            },
        },
    },
    "https://schema.org/MolecularEntity": {
        "@context": {
            **SAMPLE_CONTEXT,
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
            "uuid": "0c4c9c0c-1a76-11ef-b03b-00155d31432b",
            "aiida_version": "2.4.3",
            "creation_parameters": {
                "entities_starting_set": {
                    "node": "0e275ed7-c1ec-4926-b0d0-3b7cc97e9ab2",
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
