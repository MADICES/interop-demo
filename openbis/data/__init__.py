IDS = {
    "@openBIS.Dataset": {
        "prefix": "DS",
        "counter": 2,
    },
    "@openBIS.Experiment": {
        "prefix": "EXP",
        "counter": 2,
    },
    "@openBIS.Sample": {
        "prefix": "SAMPLE",
        "counter": 3,
    },
    "@openBIS.Object": {
        "prefix": "OBJ",
        "counter": 0,
    },
}

MAPPING = {
    "https://openbis.ont.ethz.ch/DataSet": "@openBIS.Dataset",
    "https://openbis.ont.ethz.ch/Experiment": "@openBIS.Experiment",
    "https://schema.org/Protein": "@openBIS.Sample",
    "https://schema.org/MolecularEntity": "@openBIS.Sample",
}

SAMPLE_CONTEXT = {
    "wasImported": {
        "@id": "https://schema.org/wasImported",
        "@container": "@index",
        },
    "hasChildren": {
        "@id": "http://schema.org/children",
        "@container": "@set",
    },
}

CONTEXT: dict[str, dict] = {
    "https://openbis.ont.ethz.ch/DataSet": {
        "@context": {
            "info": {
                "@id": "https://openbis.ont.ethz.ch/info",
                "@type": "xsd:string",
            },
        }
    },
    "https://openbis.ont.ethz.ch/Experiment": {
        "@context": {
            "info": {
                "@id": "https://openbis.ont.ethz.ch/info",
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
            "inChIKey": {
                "@id": "https://schema.org/inChIKey",
                "@type": "xsd:string",
            },
            "iupacName": {
                "@id": "https://schema.org/iupacName",
                "@type": "xsd:string",
            },
            "molecularFormula": {
                "@id": "https://schema.org/molecularFormula",
                "@type": "xst:string",
            },
            "molecularWeight": {
                "@id": "https://schema.org/molecularWeight",
                "@type": "xsd:float",
            },
            "molecularWeightUnits": {
                "@id": "https://schema.org/molecularWeightUnits",
                "@type": "xsd:string",
            },
        },
    },
}

DATA = [
    {
        "id": "DS-1",
        "type": "@openBIS.Dataset",
        "title": "A 1D image of some data",
        "metadata": {
            "info": "1D image",
        },
        "ontology": "https://openbis.ont.ethz.ch/DataSet",
    },
    {
        "id": "DS-2",
        "type": "@openBIS.Dataset",
        "title": "A 2D image of some data",
        "metadata": {
            "info": "2D image",
        },
        "ontology": "https://openbis.ont.ethz.ch/DataSet",
    },
    {
        "id": "EXP-1",
        "type": "@openBIS.Experiment",
        "title": "The first experiment",
        "metadata": {
            "info": "Experiment on algea",
        },
        "ontology": "https://openbis.ont.ethz.ch/Experiment",
    },
    {
        "id": "EXP-2",
        "type": "@openBIS.Experiment",
        "title": "The second experiment",
        "metadata": {
            "info": "Experiment on bacteria",
        },
        "ontology": "https://openbis.ont.ethz.ch/Experiment",
    },
    {
        "id": "SAMPLE-1",
        "type": "@openBIS.Sample",
        "title": "A protein sequence",
        "metadata": {
            "hasBioPolymerSequence": "AAACCTTTGTACAATG",
        },
        "ontology": "https://schema.org/Protein",
    },
    {
        "id": "SAMPLE-2",
        "type": "@openBIS.Sample",
        "title": "CH4 molecule",
        "metadata": {
            "inChIKey": "VNWKTOKETHGBQD-UHFFFAOYSA-N",
            "iupacName": "Methane",
            "molecularFormula": "CH4",
            "molecularWeight": 16.043,
            "molecularWeightUnits": "g/mol",
        },
        "ontology": "https://schema.org/MolecularEntity",
    },
    {
        "id": "SAMPLE-3",
        "type": "@openBIS.Sample",
        "title": "H2O molecule",
        "metadata": {
            "inChIKey": "XLYOFNOQVPJJNP-UHFFFAOYSA-N",
            "iupacName": "Water",
            "molecularFormula": "H2O",
            "molecularWeight": 18.015,
            "molecularWeightUnits": "g/mol",
        },
        "ontology": "https://schema.org/MolecularEntity",
    },
]

PLATFORMS = {
    "AiiDA": 5002,
}
