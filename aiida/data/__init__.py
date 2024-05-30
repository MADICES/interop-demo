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

OBJECT_MAPPING = {
    "https://aiida.net/Simulation": "@aiida.Simulation",
    "https://aiida.net/Workflow": "@aiida.Workflow",
    "https://schema.org/Protein": "@aiida.Sample",
    "https://schema.org/MolecularEntity": "@aiida.Sample",
}

KEY_MAPPING = {
    "https://schema.org/hasParent": "has_parent",
    "http://schema.org/children": "has_children",
    "https://schema.org/wasImported": "was_imported",
    "https://aiida.net/uuid": "uuid",
    "https://aiida.net/aiida_version": "aiida_version",
    "https://aiida.net/creation_parameters": "creation_parameters",
    "https://aiida.net/cmdline_params": "cmdline_params",
    "https://schema.org/hasBioPolymerSequence": "hasBioPolymerSequence",
    "https://schema.org/inChIKey": "key",
    "https://schema.org/iupacName": "label",
    "https://schema.org/molecularFormula": "formula",
    "https://schema.org/molecularWeight": "weight",
    "https://schema.org/molecularWeightUnits": "units",
}

OBJECT_CONTEXT = {
    "has_parent": {
        "@id": "https://schema.org/hasParent",
        "@type": "xsd:string",
    },
    "has_children": {
        "@id": "http://schema.org/children",
        "@container": "@set",
    },
    "was_imported": {
        "@id": "https://schema.org/wasImported",
        "@container": "@index",
    },
}

CONTEXT: dict[str, dict] = {
    "https://aiida.net/Simulation": {
        "@context": {
            **OBJECT_CONTEXT,
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
        },
    },
    "https://aiida.net/Workflow": {
        "@context": {
            **OBJECT_CONTEXT,
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
            **OBJECT_CONTEXT,
            "hasBioPolymerSequence": {
                "@id": "https://schema.org/hasBioPolymerSequence",
                "@type": "xsd:string",
            },
        },
    },
    "https://schema.org/MolecularEntity": {
        "@context": {
            **OBJECT_CONTEXT,
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
            "has_parent": "WF-1",
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
            "has_children": ["SIM-1"],
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
