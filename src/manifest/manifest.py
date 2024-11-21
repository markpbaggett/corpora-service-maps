from iiif_prezi3 import Manifest, config, KeyValueString
import json


class ManifestCreator:
    def __init__(self, data):
        self.data = data
        self.config = config.configs['helpers.auto_fields.AutoLang'].auto_lang = "en"
        self.label = data['title']
        self.annotations = data.get('annotations', [])
        self.metadata = self._get_metadata()
        self.manifest = self._build()

    def _get_metadata(self):
        metadata = []
        not_for_metadata = ('iiif_url', 'title', 'label', 'uri', '_search_score', 'annotations', 'date')
        for k, v in self.data.items():
            if k not in not_for_metadata and isinstance(v, str):
                values = v.split(' | ')
                metadata.append(
                    KeyValueString(
                        label=k,
                        value={"en": values}
                    )
                )
        return metadata

    def _build(self):
        manifest = Manifest(
            id=f"https://markpbaggett.github.io/corpra-service-maps/manifests/{self.data['id']}.json",
            label=self.label,
            metadata=self.metadata,
        )
        canvas = manifest.make_canvas_from_iiif(
            url=self.data['iiif_url'],
            label=f"Canvas for {self.label}",
            id=f"https://markpbaggett.github.io/corpra-service-maps/{self.data['id']}/canvas/1",
            anno_id=f"https://markpbaggett.github.io/corpra-service-maps/{self.data['id']}/canvas/1/annotation/1",
            anno_page_id=f"https://markpbaggett.github.io/corpra-service-maps/{self.data['id']}/canvas/1/annotation/1/page/1",
        )
        i = 0
        for annotation in self.annotations:
            canvas.make_annotation(
                id=f"https://markpbaggett.github.io/corpra-service-maps/{self.data['id']}/canvas/1/annotation/{i}",
                motivation="tagging",
                body={
                    "type": "TextualBody",
                    "language": "en",
                    "format": "text/plain",
                    "value": annotation["description"]},
                target=f"{canvas.id}#xywh={annotation['image_url'].split('/')[-4]}",
                anno_page_id=f"https://markpbaggett.github.io/corpra-service-maps/{self.data['id']}/canvas/1/annotation_page/{i}"
            )
            i += 1
        x = manifest.json(indent=2)
        manifest_as_json = json.loads(x)
        return manifest_as_json

    def write(self):
        with open(f'manifests/{self.data['id']}.json', 'w') as outfile:
            outfile.write(
                json.dumps(
                    self.manifest, indent=2
                )
            )
