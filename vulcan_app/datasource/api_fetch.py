import httpx


class API_fetcher:
    def __init__(self, data_service_address, data_service_token):
        self.data_service_address = data_service_address
        self.header = {'Authorization': 'Bearer ' + data_service_token}

    def fetch(self):
        response = httpx.get(self.data_service_address + '/question', headers=self.header)
        data = response.json()
        if "question" in data:
            return True, {
                "question": data["question"],
                "id": data["question_id"],
                "answer": None
            }
        else:
            return False, data["detail"] if "detail" in data else None

    def fetch_batch(self, size):
        out_data = []
        with httpx.Client(base_url=self.data_service_address, headers=self.header) as client:
            for i in range(size):
                if i % 100 == 1:
                    print(i, "/", size)
                try:
                    response = client.get('/question')
                    data = response.json()

                    if "question" in data:
                        out_data.append({
                            "question": data["question"],
                            "id": data["question_id"],
                            "answer": None
                        })
                    elif "detail" in data:
                        print(data["detail"])
                except Exception as e:
                    print(e)

        return len(out_data), out_data


if __name__ == '__main__':
    pass
