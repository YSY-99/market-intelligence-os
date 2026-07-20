from market_intel import search_sources


for recommendation in search_sources("mobile subscription conversion benchmark", limit=3):
    source = recommendation["source"]
    print("{}: {}".format(source["company"], recommendation["recommended_url"]))
