def get_changed_prices(old_price_array, new_price_array):
    old_prices = {l1.title + l1.sub_title: l1 for l1 in old_price_array}
    new_prices = {l2.title + l2.sub_title: l2 for l2 in new_price_array}
    _changed_prices = []
    for key, value in new_prices.items():
        if key in old_prices:
            old_price = old_prices[key]
            if old_price.price != value.price:
                _changed_prices.append(value)
        else:
            _changed_prices.append(value)
    return _changed_prices
