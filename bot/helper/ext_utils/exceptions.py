class DirectDownloadLinkException(Exception):
    """Tidak ditemukan metode untuk mengekstrak tautan unduhan langsung dari tautan http"""
    pass


class NotSupportedExtractionArchive(Exception):
    """Penggunaan format arsip yang mencoba mengekstrak tidak didukung"""
    pass
