import httpx
from manifest import ManifestCreator


class SearchResults:
    def __init__(self, query):
        self.query = query
        self.all = self._query()

    def _query(self):
        x = httpx.get(self.query)
        more = x.json().get('meta').get("has_next_page", False)
        page = 1
        data = {
            "results": x.json().get('records', []),
            "total": x.json().get('meta').get('total', 0),
            "num_pages": x.json().get('meta').get('num_pages', 1),
        }
        while more:
            page += 1
            x = httpx.get(f"{self.query}?page={page}")
            more = x.json().get('meta').get('has_next_page', False)
            data['results'].extend(x.json().get('records', []))
        return data


if __name__ == "__main__":
    records = SearchResults(
        "https://corpora.dh.tamu.edu/api/corpus/66d0cf276083e79367c617c6/Map/"
    )
    annotations = SearchResults(
        "https://corpora.dh.tamu.edu/api/corpus/66d0cf276083e79367c617c6/Feature/"
    )
    for annotation in annotations.all['results']:
        for work in records.all['results']:
            if work['id'] == annotation['map']['id']:
                if work.get('annotations'):
                    work['annotations'].append(annotation)
                else:
                    work['annotations'] = [annotation]
    for work in records.all['results']:
        if 'title' in work:
            x = ManifestCreator(work)
            x.write()
