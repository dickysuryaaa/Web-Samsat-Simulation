def rupiah(value):
    return "Rp {:,}".format(int(value or 0)).replace(",", ".")

