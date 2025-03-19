from iiif_prezi3 import Manifest, config, KeyValueString, Collection, load_bundled_extensions
import json
import httpx
import os

navPlace = httpx.get("http://iiif.io/api/extension/navplace/context.json", follow_redirects=True)
navplace_json = navPlace.json()

class ManifestCreator:
    def __init__(self, data):
        self.data = data
        self.extensions = load_bundled_extensions(
            extensions=[navplace_json]
        )
        self.config = config.configs['helpers.auto_fields.AutoLang'].auto_lang = "en"
        self.label = data['title']
        self.annotations = data.get('annotations', [])
        self.nav_place = data.get('nav_place', [])
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

    @staticmethod
    def _get_thumbnail(url):
        image_response = httpx.get(f"{url}/info.json", timeout=60).json()
        size = image_response['sizes'][-3]
        return {
            "id": f"{url}/full/{size['width']},/0/default.jpg",
            "width": size['width'],
            "height": size['height'],
            "type": "Image",
            "format": "image/jpeg",
            "service": [
                {
                    "id": url,
                    "type": "ImageService3",
                    "profile": "level2"
                }
            ]
        }

    def _build(self):
        try:
            thumbnail = self._get_thumbnail(self.data['iiif_url'])
            if len(self.nav_place) > 0:
                nav_place = NavPlace(self.nav_place, f"https://markpbaggett.github.io/corpora-service-maps/manifests/{self.data['id']}", self.label).features
                manifest = Manifest(
                    id=f"https://markpbaggett.github.io/corpora-service-maps/manifests/{self.data['id']}.json",
                    label=self.label,
                    metadata=self.metadata,
                    thumbnail=thumbnail,
                    partOf=[
                        {
                            "id": "https://markpbaggett.github.io/corpora-service-maps/collections/collection.json",
                            "type": "Collection"
                        }
                    ],
                    navPlace={"features": nav_place}
                )
                print(manifest)
                print("\n")
            else:
                manifest = Manifest(
                    id=f"https://markpbaggett.github.io/corpora-service-maps/manifests/{self.data['id']}.json",
                    label=self.label,
                    metadata=self.metadata,
                    thumbnail=thumbnail,
                    partOf=[
                        {
                            "id": "https://markpbaggett.github.io/corpora-service-maps/collections/collection.json",
                            "type": "Collection"
                        }
                    ]
                )
            canvas = manifest.make_canvas_from_iiif(
                url=self.data['iiif_url'],
                thumbnail=thumbnail,
                label=f"Canvas for {self.label}",
                id=f"https://markpbaggett.github.io/corpora-service-maps/{self.data['id']}/canvas/1",
                anno_id=f"https://markpbaggett.github.io/corpora-service-maps/{self.data['id']}/canvas/1/annotation/1",
                anno_page_id=f"https://markpbaggett.github.io/corpora-service-maps/{self.data['id']}/canvas/1/annotation/1/page/1",
            )
            i = 0
            for annotation in self.annotations:
                canvas.make_annotation(
                    id=f"https://markpbaggett.github.io/corpora-service-maps/{self.data['id']}/canvas/1/annotation/{i}",
                    motivation="tagging",
                    body={
                        "type": "TextualBody",
                        "language": "en",
                        "format": "text/html",
                        "value": annotation["description"]},
                    target=f"{canvas.id}#xywh={annotation['image_url'].split('/')[-4]}",
                    anno_page_id=f"https://markpbaggett.github.io/corpora-service-maps/{self.data['id']}/canvas/1/annotation_page/{i}"
                )
                i += 1
            x = manifest.json(indent=2)
            manifest_as_json = json.loads(x)
            manifest_as_json['@context'] = ["http://iiif.io/api/extension/navplace/context.json",
                                            "http://iiif.io/api/presentation/3/context.json"]
            return manifest_as_json
        except KeyError as e:
            print(f"Failed to generate manifest. Missing {e} on {self.data['title']}")

    def write(self):
        with open(f'manifests/{self.data['id']}.json', 'w') as outfile:
            outfile.write(
                json.dumps(
                    self.manifest, indent=2
                )
            )


class CollectionBuilder:
    def __init__(self, path):
        self.path = path
        self.config = config.configs['helpers.auto_fields.AutoLang'].auto_lang = "en"
        self._build_collection()

    def _build_collection(self):
        collection = Collection(
            id=f"https://markpbaggett.github.io/corpora-service-maps/collections/collection.json",
            label="World War II Service Maps",
        )
        for path, directories, files in os.walk(self.path):
            for file in files:
                with open(f'{self.path}/{file}', 'r') as new_file:
                    try:
                        data = new_file.read()
                        json_data = json.loads(data)
                        collection.make_manifest(
                            id=json_data['id'],
                            label=json_data['label']['en'][0],
                        )
                    except TypeError as e:
                        print(f"Failed to add manifest. Encountered {e} on {self.path}")
        with open('collections/collection.json', 'w') as outfile:
            outfile.write(collection.json(indent=2))


class NavPlace:
    def __init__(self, data, parent_uri, manifest_label):
        self.features = data
        self.label = manifest_label
        self.parent_uri = parent_uri
        self.features = self.__add_navplace_features()

    def __add_navplace_features(self):
        features = []
        i = 0
        for feature in self.features:
            try:
                features.append(
                    {
                        "id": f"{self.parent_uri}notdereferenceable/feature/{i}",
                        "type": "Feature",
                        "properties": {
                            "label": {
                                "en": [
                                    f"{self.label} -- {feature.get('name', '')}"
                                ]
                            }
                        },
                        "geometry": {
                            "type": "Point",
                            "coordinates": [
                                feature['coordinates'][0],
                                feature['coordinates'][1]
                            ]
                        }
                    }
                )
                i += 1
            except KeyError:
                print(f"Feature {feature} not found in locations. Add.")
                with open('errors.log', 'a') as f:
                    f.write(f'{feature}\n')
        return features