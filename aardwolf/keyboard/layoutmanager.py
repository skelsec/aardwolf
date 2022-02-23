
import json
import base64
import importlib

from aardwolf.keyboard import KeyboardLayout

### Importlib is used here, as there are many keyboard layouts and you probably don't wish to use all of them
### Importing all of them would take a considerable time however, hence dynamic loading

class KeyboardLayoutManager:
    def __init__(self):
        self.klids_to_filename = json.loads(base64.b64decode("eyIwMDE0MGMwMCAoZmYtQWRsbSkiOiAibGF5b3V0X0tCREFETE0ucHkiLCAiMDAwMDA0MWMgKHNxKSI6ICJsYXlvdXRfS0JEQUwucHkiLCAiMDAwMDA0MDEgKGFyLVNBKSI6ICJsYXlvdXRfS0JEQTEucHkiLCAiMDAwMTA0MDEgKGFyLVNBKSI6ICJsYXlvdXRfS0JEQTIucHkiLCAiMDAwMjA0MDEgKGFyLVNBKSI6ICJsYXlvdXRfS0JEQTMucHkiLCAiMDAwMDA0MmIgKGh5KSI6ICJsYXlvdXRfS0JEQVJNRS5weSIsICIwMDAyMDQyYiAoaHkpIjogImxheW91dF9rYmRhcm1waC5weSIsICIwMDAzMDQyYiAoaHkpIjogImxheW91dF9rYmRhcm10eS5weSIsICIwMDAxMDQyYiAoaHkpIjogImxheW91dF9LQkRBUk1XLnB5IiwgIjAwMDAwNDRkIChhcykiOiAibGF5b3V0X0tCRElOQVNBLnB5IiwgIjAwMDEwNDJjIChhei1MYXRuKSI6ICJsYXlvdXRfS0JEQVpTVC5weSIsICIwMDAwMDgyYyAoYXotQ3lybCkiOiAibGF5b3V0X0tCREFaRS5weSIsICIwMDAwMDQyYyAoYXotTGF0bikiOiAibGF5b3V0X0tCREFaRUwucHkiLCAiMDAwMDA0NDUgKGJuLUlOKSI6ICJsYXlvdXRfa2JkaW5iZW4ucHkiLCAiMDAwMjA0NDUgKGJuLUlOKSI6ICJsYXlvdXRfS0JESU5CRTIucHkiLCAiMDAwMTA0NDUgKGJuLUlOKSI6ICJsYXlvdXRfa2JkaW5iZTEucHkiLCAiMDAwMDA0NmQgKGJhLUN5cmwpIjogImxheW91dF9LQkRCQVNILnB5IiwgIjAwMDAwNDIzIChiZSkiOiAibGF5b3V0X0tCREJMUi5weSIsICIwMDAxMDgwYyAoZnItQkUpIjogImxheW91dF9LQkRCRU5FLnB5IiwgIjAwMDAwODBjIChmci1CRSkiOiAibGF5b3V0X0tCREJFLnB5IiwgIjAwMDAwODEzIChubC1CRSkiOiAibGF5b3V0X0tCREJFLnB5IiwgIjAwMDAyMDFhIChicy1DeXJsKSI6ICJsYXlvdXRfa2JkYmhjLnB5IiwgIjAwMGIwYzAwIChidWctQnVnaSkiOiAibGF5b3V0X0tCREJVRy5weSIsICIwMDAzMDQwMiAoYmcpIjogImxheW91dF9LQkRCVUxHLnB5IiwgIjAwMDEwNDAyIChiZykiOiAibGF5b3V0X0tCRFVTLnB5IiwgIjAwMDAwNDA0ICh6aC1IYW50LVRXKSI6ICJsYXlvdXRfS0JEVVMucHkiLCAiMDAwMDA0MDkgKGVuLVVTKSI6ICJsYXlvdXRfS0JEVVMucHkiLCAiMDAwMDA4MDQgKHpoLUhhbnMtQ04pIjogImxheW91dF9LQkRVUy5weSIsICIwMDAwMGMwNCAoemgtSGFudC1ISykiOiAibGF5b3V0X0tCRFVTLnB5IiwgIjAwMDAxMDA0ICh6aC1IYW5zLVNHKSI6ICJsYXlvdXRfS0JEVVMucHkiLCAiMDAwMDE0MDQgKHpoLUhhbnQtTU8pIjogImxheW91dF9LQkRVUy5weSIsICIwMDA0MDQwMiAoYmcpIjogImxheW91dF9LQkRCR1BIMS5weSIsICIwMDAyMDQwMiAoYmcpIjogImxheW91dF9LQkRCR1BILnB5IiwgIjAwMDAwNDAyIChiZykiOiAibGF5b3V0X0tCREJVLnB5IiwgIjAwMDAxMDA5IChlbi1DQSkiOiAibGF5b3V0X0tCRENBLnB5IiwgIjAwMDAwYzBjIChmci1DQSkiOiAibGF5b3V0X0tCREZDLnB5IiwgIjAwMDExMDA5IChlbi1DQSkiOiAibGF5b3V0X0tCRENBTi5weSIsICIwMDAwMDg1ZiAodHptLUxhdG4pIjogImxheW91dF9LQkRUWk0ucHkiLCAiMDAwMDA0OTIgKGt1LUFyYWIpIjogImxheW91dF9LQkRLVVJELnB5IiwgIjAwMDAwNDA1IChjcykiOiAibGF5b3V0X0tCRENaLnB5IiwgIjAwMDEwNDA1IChjcykiOiAibGF5b3V0X0tCRENaMS5weSIsICIwMDAyMDQwNSAoY3MpIjogImxheW91dF9LQkRDWjIucHkiLCAiMDAwMDA0NWMgKGNoci1DaGVyKSI6ICJsYXlvdXRfS0JEQ0hFUi5weSIsICIwMDAxMDQ1YyAoY2hyLUNoZXIpIjogImxheW91dF9LQkRDSEVSUC5weSIsICIwMDAwMDQwNiAoZGEpIjogImxheW91dF9LQkREQS5weSIsICIwMDAwMDQzOSAoaGkpIjogImxheW91dF9LQkRJTkRFVi5weSIsICIwMDAwMDQ2NSAoZHYpIjogImxheW91dF9LQkRESVYxLnB5IiwgIjAwMDEwNDY1IChkdikiOiAibGF5b3V0X0tCRERJVjIucHkiLCAiMDAwMDA0MTMgKG5sLU5MKSI6ICJsYXlvdXRfa2JkbmUucHkiLCAiMDAwMDBjNTEgKGR6KSI6ICJsYXlvdXRfS0JERFpPLnB5IiwgIjAwMDA0MDA5IChlbi1JTikiOiAibGF5b3V0X0tCRElORU4ucHkiLCAiMDAwMDA0MjUgKGV0KSI6ICJsYXlvdXRfS0JERVNULnB5IiwgIjAwMDAwNDM4IChmbykiOiAibGF5b3V0X0tCREZPLnB5IiwgIjAwMDAwNDBiIChmaSkiOiAibGF5b3V0X0tCREZJLnB5IiwgIjAwMDAwODNiIChzZS1MYXRuLVNFKSI6ICJsYXlvdXRfa2JkZmkxLnB5IiwgIjAwMDEwODNiIChzZS1MYXRuLVNFKSI6ICJsYXlvdXRfa2JkZmkxLnB5IiwgIjAwMDAwNDBjIChmci1GUikiOiAibGF5b3V0X0tCREZSLnB5IiwgIjAwMTIwYzAwIChnZW0tUnVucikiOiAibGF5b3V0X0tCREZUSFJLLnB5IiwgIjAwMDIwNDM3IChrYSkiOiAibGF5b3V0X2tiZGdlb2VyLnB5IiwgIjAwMDAwNDM3IChrYSkiOiAibGF5b3V0X0tCREdFTy5weSIsICIwMDAzMDQzNyAoa2EpIjogImxheW91dF9rYmRnZW9tZS5weSIsICIwMDA0MDQzNyAoa2EpIjogImxheW91dF9rYmRnZW9vYS5weSIsICIwMDAxMDQzNyAoa2EpIjogImxheW91dF9rYmRnZW9xdy5weSIsICIwMDAwMDQwNyAoZGUtREUpIjogImxheW91dF9LQkRHUi5weSIsICIwMDAxMDQwNyAoZGUtREUpIjogImxheW91dF9LQkRHUjEucHkiLCAiMDAwYzBjMDAgKGdvdC1Hb3RoKSI6ICJsYXlvdXRfS0JER1RIQy5weSIsICIwMDAwMDQwOCAoZWwpIjogImxheW91dF9LQkRIRS5weSIsICIwMDAxMDQwOCAoZWwpIjogImxheW91dF9LQkRIRTIyMC5weSIsICIwMDAzMDQwOCAoZWwpIjogImxheW91dF9LQkRIRUxBMi5weSIsICIwMDAyMDQwOCAoZWwpIjogImxheW91dF9LQkRIRTMxOS5weSIsICIwMDA0MDQwOCAoZWwpIjogImxheW91dF9LQkRIRUxBMy5weSIsICIwMDA1MDQwOCAoZWwpIjogImxheW91dF9LQkRHS0wucHkiLCAiMDAwNjA0MDggKGVsKSI6ICJsYXlvdXRfS0JESEVQVC5weSIsICIwMDAwMDQ2ZiAoa2wpIjogImxheW91dF9LQkRHUkxORC5weSIsICIwMDAwMDQ3NCAoZ24pIjogImxheW91dF9LQkRHTi5weSIsICIwMDAwMDQ0NyAoZ3UpIjogImxheW91dF9LQkRJTkdVSi5weSIsICIwMDAwMDQ2OCAoaGEtTGF0bikiOiAibGF5b3V0X0tCREhBVS5weSIsICIwMDAwMDQ3NSAoaGF3LUxhdG4pIjogImxheW91dF9LQkRIQVcucHkiLCAiMDAwMDA0MGQgKGhlKSI6ICJsYXlvdXRfS0JESEVCLnB5IiwgIjAwMDIwNDBkIChoZSkiOiAibGF5b3V0X2tiZGhlYmwzLnB5IiwgIjAwMDEwNDM5IChoaSkiOiAibGF5b3V0X0tCRElOSElOLnB5IiwgIjAwMDAwNDBlIChodSkiOiAibGF5b3V0X0tCREhVLnB5IiwgIjAwMDEwNDBlIChodSkiOiAibGF5b3V0X0tCREhVMS5weSIsICIwMDAwMDQwZiAoaXMpIjogImxheW91dF9LQkRJQy5weSIsICIwMDAwMDQ3MCAoaWctTGF0bikiOiAibGF5b3V0X0tCRElCTy5weSIsICIwMDAwMDg1ZCAoaXUtTGF0bikiOiAibGF5b3V0X0tCRElVTEFULnB5IiwgIjAwMDEwNDVkIChpdS1DYW5zKSI6ICJsYXlvdXRfS0JESU5VSzIucHkiLCAiMDAwMDE4MDkgKGVuLUlFKSI6ICJsYXlvdXRfS0JESVIucHkiLCAiMDAwMDA0MTAgKGl0LUlUKSI6ICJsYXlvdXRfS0JESVQucHkiLCAiMDAwMTA0MTAgKGl0LUlUKSI6ICJsYXlvdXRfS0JESVQxNDIucHkiLCAiMDAwMDA0MTEgKGphKSI6ICJsYXlvdXRfS0JESlBOLnB5IiwgIjAwMTEwYzAwIChqdi1KYXZhKSI6ICJsYXlvdXRfS0JESkFWLnB5IiwgIjAwMDAwNDRiIChrbikiOiAibGF5b3V0X0tCRElOS0FOLnB5IiwgIjAwMDAwNDNmIChraykiOiAibGF5b3V0X0tCREtBWi5weSIsICIwMDAwMDQ1MyAoa20pIjogImxheW91dF9LQkRLSE1SLnB5IiwgIjAwMDEwNDUzIChrbSkiOiAibGF5b3V0X0tCREtOSS5weSIsICIwMDAwMDQxMiAoa28pIjogImxheW91dF9LQkRLT1IucHkiLCAiMDAwMDA0NDAgKGt5LUN5cmwpIjogImxheW91dF9LQkRLWVIucHkiLCAiMDAwMDA0NTQgKGxvKSI6ICJsYXlvdXRfS0JETEFPLnB5IiwgIjAwMDAwODBhIChlcy1NWCkiOiAibGF5b3V0X0tCRExBLnB5IiwgIjAwMDAwNDI2IChsdikiOiAibGF5b3V0X0tCRExWLnB5IiwgIjAwMDEwNDI2IChsdikiOiAibGF5b3V0X0tCRExWMS5weSIsICIwMDAyMDQyNiAobHYpIjogImxheW91dF9LQkRMVlNULnB5IiwgIjAwMDcwYzAwIChsaXMtTGlzdSkiOiAibGF5b3V0X2tiZGxpc3ViLnB5IiwgIjAwMDgwYzAwIChsaXMtTGlzdSkiOiAibGF5b3V0X2tiZGxpc3VzLnB5IiwgIjAwMDEwNDI3IChsdCkiOiAibGF5b3V0X0tCRExUMS5weSIsICIwMDAwMDQyNyAobHQpIjogImxheW91dF9LQkRMVC5weSIsICIwMDAyMDQyNyAobHQpIjogImxheW91dF9LQkRMVDIucHkiLCAiMDAwMDA0NmUgKGxiKSI6ICJsYXlvdXRfS0JEU0YucHkiLCAiMDAwMDEwMGMgKGZyLUNIKSI6ICJsYXlvdXRfS0JEU0YucHkiLCAiMDAwMDA0MmYgKG1rKSI6ICJsYXlvdXRfS0JETUFDLnB5IiwgIjAwMDEwNDJmIChtaykiOiAibGF5b3V0X0tCRE1BQ1NULnB5IiwgIjAwMDAwNDRjIChtbCkiOiAibGF5b3V0X2tiZGlubWFsLnB5IiwgIjAwMDAwNDNhIChtdCkiOiAibGF5b3V0X2tiZG1sdDQ3LnB5IiwgIjAwMDEwNDNhIChtdCkiOiAibGF5b3V0X2tiZG1sdDQ4LnB5IiwgIjAwMDAwNDgxIChtaS1MYXRuKSI6ICJsYXlvdXRfa2JkbWFvcmkucHkiLCAiMDAwMDE0MDkgKGVuLU5aKSI6ICJsYXlvdXRfa2JkbWFvcmkucHkiLCAiMDAwMDA0NGUgKG1yKSI6ICJsYXlvdXRfS0JESU5NQVIucHkiLCAiMDAwMDA4NTAgKG1uLU1vbmcpIjogImxheW91dF9LQkRNT05NTy5weSIsICIwMDAwMDQ1MCAobW4tQ3lybCkiOiAibGF5b3V0X0tCRE1PTi5weSIsICIwMDAxMGMwMCAobXkpIjogImxheW91dF9LQkRNWUFOLnB5IiwgIjAwMTMwYzAwIChteSkiOiAibGF5b3V0X0tCRE1ZQU4ucHkiLCAiMDAwOTBjMDAgKG5xbykiOiAibGF5b3V0X2tiZG5rby5weSIsICIwMDAwMDQ2MSAobmUtTlApIjogImxheW91dF9rYmRuZXByLnB5IiwgIjAwMDIwYzAwIChraGItVGFsdSkiOiAibGF5b3V0X0tCRE5UTC5weSIsICIwMDAwMDQxNCAobmIpIjogImxheW91dF9LQkROTy5weSIsICIwMDAwMDQzYiAoc2UtTGF0bi1OTykiOiAibGF5b3V0X2tiZG5vMS5weSIsICIwMDAwMDQ0OCAob3IpIjogImxheW91dF9LQkRJTk9SSS5weSIsICIwMDA0MGMwMCAoc2dhLU9nYW0pIjogImxheW91dF9LQkRPR0hBTS5weSIsICIwMDBkMGMwMCAoc2F0LU9sY2spIjogImxheW91dF9LQkRPTENILnB5IiwgIjAwMGYwYzAwIChldHQtSXRhbCkiOiAibGF5b3V0X0tCRE9MRElULnB5IiwgIjAwMTUwYzAwIChvc2EtT3NnZSkiOiAibGF5b3V0X0tCRE9TQS5weSIsICIwMDBlMGMwMCAoc28tT3NtYSkiOiAibGF5b3V0X0tCRE9TTS5weSIsICIwMDAwMDQ2MyAocHMpIjogImxheW91dF9rYmRwYXNoLnB5IiwgIjAwMDAwNDI5IChmYSkiOiAibGF5b3V0X0tCREZBLnB5IiwgIjAwMDUwNDI5IChmYSkiOiAibGF5b3V0X2tiZGZhci5weSIsICIwMDBhMGMwMCAobW4tUGhhZykiOiAibGF5b3V0X2tiZHBoYWdzLnB5IiwgIjAwMDEwNDE1IChwbCkiOiAibGF5b3V0X0tCRFBMLnB5IiwgIjAwMDAwNDE1IChwbCkiOiAibGF5b3V0X0tCRFBMMS5weSIsICIwMDAwMDgxNiAocHQtUFQpIjogImxheW91dF9LQkRQTy5weSIsICIwMDAwMDQxNiAocHQtQlIpIjogImxheW91dF9LQkRCUi5weSIsICIwMDAxMDQxNiAocHQtQlIpIjogImxheW91dF9LQkRCUi5weSIsICIwMDAwMDQ0NiAocGEpIjogImxheW91dF9LQkRJTlBVTi5weSIsICIwMDAwMDQxOCAocm8tUk8pIjogImxheW91dF9LQkRSTy5weSIsICIwMDAyMDQxOCAocm8tUk8pIjogImxheW91dF9LQkRST1BSLnB5IiwgIjAwMDEwNDE4IChyby1STykiOiAibGF5b3V0X0tCRFJPU1QucHkiLCAiMDAwMDA0MTkgKHJ1KSI6ICJsYXlvdXRfS0JEUlUucHkiLCAiMDAwMjA0MTkgKHJ1KSI6ICJsYXlvdXRfS0JEUlVNLnB5IiwgIjAwMDEwNDE5IChydSkiOiAibGF5b3V0X0tCRFJVMS5weSIsICIwMDAwMDQ4NSAoc2FoLUN5cmwpIjogImxheW91dF9LQkRZQUsucHkiLCAiMDAwMjA4M2IgKHNlLUxhdG4tU0UpIjogImxheW91dF9rYmRzbXNmaS5weSIsICIwMDAxMDQzYiAoc2UtTGF0bi1OTykiOiAibGF5b3V0X2tiZHNtc25vLnB5IiwgIjAwMDExODA5IChlbi1JRSkiOiAibGF5b3V0X0tCREdBRS5weSIsICIwMDAwMGMxYSAoc3ItQ3lybC1DUykiOiAibGF5b3V0X0tCRFlDQy5weSIsICIwMDAwMDgxYSAoc3ItTGF0bi1DUykiOiAibGF5b3V0X0tCRFlDTC5weSIsICIwMDAwMDQzMiAodG4tWkEpIjogImxheW91dF9LQkROU08ucHkiLCAiMDAwMDA0NmMgKG5zbykiOiAibGF5b3V0X0tCRE5TTy5weSIsICIwMDAwMDQ1YiAoc2kpIjogImxheW91dF9LQkRTTjEucHkiLCAiMDAwMTA0NWIgKHNpKSI6ICJsYXlvdXRfS0JEU1cwOS5weSIsICIwMDAwMDQxYiAoc2spIjogImxheW91dF9LQkRTTC5weSIsICIwMDAxMDQxYiAoc2spIjogImxheW91dF9LQkRTTDEucHkiLCAiMDAwMDA0MWEgKGhyLUhSKSI6ICJsYXlvdXRfS0JEQ1IucHkiLCAiMDAwMDA0MjQgKHNsKSI6ICJsYXlvdXRfS0JEQ1IucHkiLCAiMDAxMDBjMDAgKHNyYi1Tb3JhKSI6ICJsYXlvdXRfS0JEU09SQS5weSIsICIwMDAxMDQyZSAoaHNiKSI6ICJsYXlvdXRfS0JEU09SRVgucHkiLCAiMDAwMjA0MmUgKGhzYikiOiAibGF5b3V0X0tCRFNPUlMxLnB5IiwgIjAwMDAwNDJlIChoc2IpIjogImxheW91dF9LQkRTT1JTVC5weSIsICIwMDAwMDQwYSAoZXMtRVMpIjogImxheW91dF9LQkRTUC5weSIsICIwMDAxMDQwYSAoZXMtRVMpIjogImxheW91dF9LQkRFUy5weSIsICIwMDAwMDQxZCAoc3YtU0UpIjogImxheW91dF9LQkRTVy5weSIsICIwMDAwMDgwNyAoZGUtQ0gpIjogImxheW91dF9LQkRTRy5weSIsICIwMDAwMDQ1YSAoc3lyLVN5cmMpIjogImxheW91dF9LQkRTWVIxLnB5IiwgIjAwMDEwNDVhIChzeXItU3lyYykiOiAibGF5b3V0X0tCRFNZUjIucHkiLCAiMDAwMzBjMDAgKHRkZC1UYWxlKSI6ICJsYXlvdXRfS0JEVEFJTEUucHkiLCAiMDAwMDA0MjggKHRnLUN5cmwpIjogImxheW91dF9LQkRUQUpJSy5weSIsICIwMDAwMDQ0OSAodGEtSU4pIjogImxheW91dF9LQkRJTlRBTS5weSIsICIwMDAyMDQ0OSAodGEtSU4pIjogImxheW91dF9LQkRUQU05OS5weSIsICIwMDAxMDQ0NCAodHQtQ3lybCkiOiAibGF5b3V0X0tCRFRUMTAyLnB5IiwgIjAwMDAwNDQ0ICh0dC1DeXJsKSI6ICJsYXlvdXRfS0JEVEFULnB5IiwgIjAwMDAwNDRhICh0ZSkiOiAibGF5b3V0X0tCRElOVEVMLnB5IiwgIjAwMDAwNDFlICh0aCkiOiAibGF5b3V0X0tCRFRIMC5weSIsICIwMDAyMDQxZSAodGgpIjogImxheW91dF9LQkRUSDIucHkiLCAiMDAwMTA0MWUgKHRoKSI6ICJsYXlvdXRfS0JEVEgxLnB5IiwgIjAwMDMwNDFlICh0aCkiOiAibGF5b3V0X0tCRFRIMy5weSIsICIwMDAwMDQ1MSAoYm8tVGlidCkiOiAibGF5b3V0X0tCRFRJUFJDLnB5IiwgIjAwMDEwNDUxIChiby1UaWJ0KSI6ICJsYXlvdXRfS0JEVElQUkQucHkiLCAiMDAwMDEwNWYgKHR6bS1UZm5nKSI6ICJsYXlvdXRfS0JEVElGSS5weSIsICIwMDAxMTA1ZiAodHptLVRmbmcpIjogImxheW91dF9LQkRUSUZJMi5weSIsICIwMDAxMDg1MCAobW4tTW9uZykiOiAibGF5b3V0X0tCRE1PTlNULnB5IiwgIjAwMDEwNDFmICh0cikiOiAibGF5b3V0X0tCRFRVRi5weSIsICIwMDAwMDQxZiAodHIpIjogImxheW91dF9LQkRUVVEucHkiLCAiMDAwMDA0NDIgKHRrLUxhdG4pIjogImxheW91dF9LQkRUVVJNRS5weSIsICIwMDAwMDQyMiAodWspIjogImxheW91dF9LQkRVUi5weSIsICIwMDAyMDQyMiAodWspIjogImxheW91dF9LQkRVUjEucHkiLCAiMDAwMDA4MDkgKGVuLUdCKSI6ICJsYXlvdXRfS0JEVUsucHkiLCAiMDAwMDA0NTIgKGN5KSI6ICJsYXlvdXRfa2JkdWt4LnB5IiwgIjAwMDEwNDA5IChlbi1VUykiOiAibGF5b3V0X0tCRERWLnB5IiwgIjAwMDMwNDA5IChlbi1VUykiOiAibGF5b3V0X0tCRFVTTC5weSIsICIwMDA0MDQwOSAoZW4tVVMpIjogImxheW91dF9LQkRVU1IucHkiLCAiMDAwMjA0MDkgKGVuLVVTKSI6ICJsYXlvdXRfS0JEVVNYLnB5IiwgIjAwMDAwNDIwICh1ci1QSykiOiAibGF5b3V0X0tCRFVSRFUucHkiLCAiMDAwNTA0MDkgKGVuLVVTKSI6ICJsYXlvdXRfS0JEVVNBLnB5IiwgIjAwMDEwNDgwICh1Zy1BcmFiKSI6ICJsYXlvdXRfS0JEVUdIUjEucHkiLCAiMDAwMDA0ODAgKHVnLUFyYWIpIjogImxheW91dF9LQkRVR0hSLnB5IiwgIjAwMDAwODQzICh1ei1DeXJsKSI6ICJsYXlvdXRfS0JEVVpCLnB5IiwgIjAwMDAwNDJhICh2aSkiOiAibGF5b3V0X0tCRFZOVEMucHkiLCAiMDAwMDA0ODggKHdvLUxhdG4pIjogImxheW91dF9LQkRXT0wucHkiLCAiMDAwMDA0NmEgKHlvLUxhdG4pIjogImxheW91dF9LQkRZQkEucHkifQ==").decode())
        self.names_to_filename = json.loads(base64.b64decode("eyJBRExhTSI6ICJsYXlvdXRfS0JEQURMTS5weSIsICJBbGJhbmlhbiI6ICJsYXlvdXRfS0JEQUwucHkiLCAiQXJhYmljICgxMDEpIjogImxheW91dF9LQkRBMS5weSIsICJBcmFiaWMgKDEwMikiOiAibGF5b3V0X0tCREEyLnB5IiwgIkFyYWJpYyAoMTAyKSBBWkVSVFkiOiAibGF5b3V0X0tCREEzLnB5IiwgIkFybWVuaWFuIEVhc3Rlcm4gKExlZ2FjeSkiOiAibGF5b3V0X0tCREFSTUUucHkiLCAiQXJtZW5pYW4gUGhvbmV0aWMiOiAibGF5b3V0X2tiZGFybXBoLnB5IiwgIkFybWVuaWFuIFR5cGV3cml0ZXIiOiAibGF5b3V0X2tiZGFybXR5LnB5IiwgIkFybWVuaWFuIFdlc3Rlcm4gKExlZ2FjeSkiOiAibGF5b3V0X0tCREFSTVcucHkiLCAiQXNzYW1lc2UgLSBJTlNDUklQVCI6ICJsYXlvdXRfS0JESU5BU0EucHkiLCAiQXplcmJhaWphbmkgKFN0YW5kYXJkKSI6ICJsYXlvdXRfS0JEQVpTVC5weSIsICJBemVyYmFpamFuaSBDeXJpbGxpYyI6ICJsYXlvdXRfS0JEQVpFLnB5IiwgIkF6ZXJiYWlqYW5pIExhdGluIjogImxheW91dF9LQkRBWkVMLnB5IiwgIkJhbmdsYSI6ICJsYXlvdXRfa2JkaW5iZW4ucHkiLCAiQmFuZ2xhIC0gSU5TQ1JJUFQiOiAibGF5b3V0X0tCRElOQkUyLnB5IiwgIkJhbmdsYSAtIElOU0NSSVBUIChMZWdhY3kpIjogImxheW91dF9rYmRpbmJlMS5weSIsICJCYXNoa2lyIjogImxheW91dF9LQkRCQVNILnB5IiwgIkJlbGFydXNpYW4iOiAibGF5b3V0X0tCREJMUi5weSIsICJCZWxnaWFuIChDb21tYSkiOiAibGF5b3V0X0tCREJFTkUucHkiLCAiQmVsZ2lhbiBGcmVuY2giOiAibGF5b3V0X0tCREJFLnB5IiwgIkJlbGdpYW4gKFBlcmlvZCkiOiAibGF5b3V0X0tCREJFLnB5IiwgIkJvc25pYW4gKEN5cmlsbGljKSI6ICJsYXlvdXRfa2JkYmhjLnB5IiwgIkJ1Z2luZXNlIjogImxheW91dF9LQkRCVUcucHkiLCAiQnVsZ2FyaWFuIjogImxheW91dF9LQkRCVUxHLnB5IiwgIkJ1bGdhcmlhbiAoTGF0aW4pIjogImxheW91dF9LQkRVUy5weSIsICJDaGluZXNlIChUcmFkaXRpb25hbCkgLSBVUyI6ICJsYXlvdXRfS0JEVVMucHkiLCAiVVMiOiAibGF5b3V0X0tCRFVTLnB5IiwgIkNoaW5lc2UgKFNpbXBsaWZpZWQpIC0gVVMiOiAibGF5b3V0X0tCRFVTLnB5IiwgIkNoaW5lc2UgKFRyYWRpdGlvbmFsLCBIb25nIEtvbmcgUy5BLlIuKSAtIFVTIjogImxheW91dF9LQkRVUy5weSIsICJDaGluZXNlIChTaW1wbGlmaWVkLCBTaW5nYXBvcmUpIC0gVVMiOiAibGF5b3V0X0tCRFVTLnB5IiwgIkNoaW5lc2UgKFRyYWRpdGlvbmFsLCBNYWNhbyBTLkEuUi4pIC0gVVMiOiAibGF5b3V0X0tCRFVTLnB5IiwgIkJ1bGdhcmlhbiAoUGhvbmV0aWMgVHJhZGl0aW9uYWwpIjogImxheW91dF9LQkRCR1BIMS5weSIsICJCdWxnYXJpYW4gKFBob25ldGljKSI6ICJsYXlvdXRfS0JEQkdQSC5weSIsICJCdWxnYXJpYW4gKFR5cGV3cml0ZXIpIjogImxheW91dF9LQkRCVS5weSIsICJDYW5hZGlhbiBGcmVuY2giOiAibGF5b3V0X0tCRENBLnB5IiwgIkNhbmFkaWFuIEZyZW5jaCAoTGVnYWN5KSI6ICJsYXlvdXRfS0JERkMucHkiLCAiQ2FuYWRpYW4gTXVsdGlsaW5ndWFsIFN0YW5kYXJkIjogImxheW91dF9LQkRDQU4ucHkiLCAiQ2VudHJhbCBBdGxhcyBUYW1hemlnaHQiOiAibGF5b3V0X0tCRFRaTS5weSIsICJDZW50cmFsIEt1cmRpc2giOiAibGF5b3V0X0tCREtVUkQucHkiLCAiQ3plY2giOiAibGF5b3V0X0tCRENaLnB5IiwgIkN6ZWNoIChRV0VSVFkpIjogImxheW91dF9LQkRDWjEucHkiLCAiQ3plY2ggUHJvZ3JhbW1lcnMiOiAibGF5b3V0X0tCRENaMi5weSIsICJDaGVyb2tlZSBOYXRpb24iOiAibGF5b3V0X0tCRENIRVIucHkiLCAiQ2hlcm9rZWUgUGhvbmV0aWMiOiAibGF5b3V0X0tCRENIRVJQLnB5IiwgIkRhbmlzaCI6ICJsYXlvdXRfS0JEREEucHkiLCAiRGV2YW5hZ2FyaSAtIElOU0NSSVBUIjogImxheW91dF9LQkRJTkRFVi5weSIsICJEaXZlaGkgUGhvbmV0aWMiOiAibGF5b3V0X0tCRERJVjEucHkiLCAiRGl2ZWhpIFR5cGV3cml0ZXIiOiAibGF5b3V0X0tCRERJVjIucHkiLCAiRHV0Y2giOiAibGF5b3V0X2tiZG5lLnB5IiwgIkR6b25na2hhIjogImxheW91dF9LQkREWk8ucHkiLCAiRW5nbGlzaCAoSW5kaWEpIjogImxheW91dF9LQkRJTkVOLnB5IiwgIkVzdG9uaWFuIjogImxheW91dF9LQkRFU1QucHkiLCAiRmFlcm9lc2UiOiAibGF5b3V0X0tCREZPLnB5IiwgIkZpbm5pc2giOiAibGF5b3V0X0tCREZJLnB5IiwgIlN3ZWRpc2ggd2l0aCBTYW1pIjogImxheW91dF9rYmRmaTEucHkiLCAiRmlubmlzaCB3aXRoIFNhbWkiOiAibGF5b3V0X2tiZGZpMS5weSIsICJGcmVuY2giOiAibGF5b3V0X0tCREZSLnB5IiwgIkZ1dGhhcmsiOiAibGF5b3V0X0tCREZUSFJLLnB5IiwgIkdlb3JnaWFuIChFcmdvbm9taWMpIjogImxheW91dF9rYmRnZW9lci5weSIsICJHZW9yZ2lhbiAoTGVnYWN5KSI6ICJsYXlvdXRfS0JER0VPLnB5IiwgIkdlb3JnaWFuIChNRVMpIjogImxheW91dF9rYmRnZW9tZS5weSIsICJHZW9yZ2lhbiAoT2xkIEFscGhhYmV0cykiOiAibGF5b3V0X2tiZGdlb29hLnB5IiwgIkdlb3JnaWFuIChRV0VSVFkpIjogImxheW91dF9rYmRnZW9xdy5weSIsICJHZXJtYW4iOiAibGF5b3V0X0tCREdSLnB5IiwgIkdlcm1hbiAoSUJNKSI6ICJsYXlvdXRfS0JER1IxLnB5IiwgIkdvdGhpYyI6ICJsYXlvdXRfS0JER1RIQy5weSIsICJHcmVlayI6ICJsYXlvdXRfS0JESEUucHkiLCAiR3JlZWsgKDIyMCkiOiAibGF5b3V0X0tCREhFMjIwLnB5IiwgIkdyZWVrICgyMjApIExhdGluIjogImxheW91dF9LQkRIRUxBMi5weSIsICJHcmVlayAoMzE5KSI6ICJsYXlvdXRfS0JESEUzMTkucHkiLCAiR3JlZWsgKDMxOSkgTGF0aW4iOiAibGF5b3V0X0tCREhFTEEzLnB5IiwgIkdyZWVrIExhdGluIjogImxheW91dF9LQkRHS0wucHkiLCAiR3JlZWsgUG9seXRvbmljIjogImxheW91dF9LQkRIRVBULnB5IiwgIkdyZWVubGFuZGljIjogImxheW91dF9LQkRHUkxORC5weSIsICJHdWFyYW5pIjogImxheW91dF9LQkRHTi5weSIsICJHdWphcmF0aSI6ICJsYXlvdXRfS0JESU5HVUoucHkiLCAiSGF1c2EiOiAibGF5b3V0X0tCREhBVS5weSIsICJIYXdhaWlhbiI6ICJsYXlvdXRfS0JESEFXLnB5IiwgIkhlYnJldyI6ICJsYXlvdXRfS0JESEVCLnB5IiwgIkhlYnJldyAoU3RhbmRhcmQpIjogImxheW91dF9rYmRoZWJsMy5weSIsICJIaW5kaSBUcmFkaXRpb25hbCI6ICJsYXlvdXRfS0JESU5ISU4ucHkiLCAiSHVuZ2FyaWFuIjogImxheW91dF9LQkRIVS5weSIsICJIdW5nYXJpYW4gMTAxLWtleSI6ICJsYXlvdXRfS0JESFUxLnB5IiwgIkljZWxhbmRpYyI6ICJsYXlvdXRfS0JESUMucHkiLCAiSWdibyI6ICJsYXlvdXRfS0JESUJPLnB5IiwgIkludWt0aXR1dCAtIExhdGluIjogImxheW91dF9LQkRJVUxBVC5weSIsICJJbnVrdGl0dXQgLSBOYXFpdHRhdXQiOiAibGF5b3V0X0tCRElOVUsyLnB5IiwgIklyaXNoIjogImxheW91dF9LQkRJUi5weSIsICJJdGFsaWFuIjogImxheW91dF9LQkRJVC5weSIsICJJdGFsaWFuICgxNDIpIjogImxheW91dF9LQkRJVDE0Mi5weSIsICJKYXBhbmVzZSI6ICJsYXlvdXRfS0JESlBOLnB5IiwgIkphdmFuZXNlIjogImxheW91dF9LQkRKQVYucHkiLCAiS2FubmFkYSI6ICJsYXlvdXRfS0JESU5LQU4ucHkiLCAiS2F6YWtoIjogImxheW91dF9LQkRLQVoucHkiLCAiS2htZXIiOiAibGF5b3V0X0tCREtITVIucHkiLCAiS2htZXIgKE5JREEpIjogImxheW91dF9LQkRLTkkucHkiLCAiS29yZWFuIjogImxheW91dF9LQkRLT1IucHkiLCAiS3lyZ3l6IEN5cmlsbGljIjogImxheW91dF9LQkRLWVIucHkiLCAiTGFvIjogImxheW91dF9LQkRMQU8ucHkiLCAiTGF0aW4gQW1lcmljYW4iOiAibGF5b3V0X0tCRExBLnB5IiwgIkxhdHZpYW4iOiAibGF5b3V0X0tCRExWLnB5IiwgIkxhdHZpYW4gKFFXRVJUWSkiOiAibGF5b3V0X0tCRExWMS5weSIsICJMYXR2aWFuIChTdGFuZGFyZCkiOiAibGF5b3V0X0tCRExWU1QucHkiLCAiTGlzdSAoQmFzaWMpIjogImxheW91dF9rYmRsaXN1Yi5weSIsICJMaXN1IChTdGFuZGFyZCkiOiAibGF5b3V0X2tiZGxpc3VzLnB5IiwgIkxpdGh1YW5pYW4iOiAibGF5b3V0X0tCRExUMS5weSIsICJMaXRodWFuaWFuIElCTSI6ICJsYXlvdXRfS0JETFQucHkiLCAiTGl0aHVhbmlhbiBTdGFuZGFyZCI6ICJsYXlvdXRfS0JETFQyLnB5IiwgIkx1eGVtYm91cmdpc2giOiAibGF5b3V0X0tCRFNGLnB5IiwgIlN3aXNzIEZyZW5jaCI6ICJsYXlvdXRfS0JEU0YucHkiLCAiTWFjZWRvbmlhbiI6ICJsYXlvdXRfS0JETUFDLnB5IiwgIk1hY2Vkb25pYW4gLSBTdGFuZGFyZCI6ICJsYXlvdXRfS0JETUFDU1QucHkiLCAiTWFsYXlhbGFtIjogImxheW91dF9rYmRpbm1hbC5weSIsICJNYWx0ZXNlIDQ3LUtleSI6ICJsYXlvdXRfa2JkbWx0NDcucHkiLCAiTWFsdGVzZSA0OC1LZXkiOiAibGF5b3V0X2tiZG1sdDQ4LnB5IiwgIk1hb3JpIjogImxheW91dF9rYmRtYW9yaS5weSIsICJOWiBBb3RlYXJvYSI6ICJsYXlvdXRfa2JkbWFvcmkucHkiLCAiTWFyYXRoaSI6ICJsYXlvdXRfS0JESU5NQVIucHkiLCAiTW9uZ29saWFuIChNb25nb2xpYW4gU2NyaXB0KSI6ICJsYXlvdXRfS0JETU9OTU8ucHkiLCAiTW9uZ29saWFuIEN5cmlsbGljIjogImxheW91dF9LQkRNT04ucHkiLCAiTXlhbm1hciAoUGhvbmV0aWMgb3JkZXIpIjogImxheW91dF9LQkRNWUFOLnB5IiwgIk15YW5tYXIgKFZpc3VhbCBvcmRlcikiOiAibGF5b3V0X0tCRE1ZQU4ucHkiLCAiTlx1MjAxOUtvIjogImxheW91dF9rYmRua28ucHkiLCAiTmVwYWxpIjogImxheW91dF9rYmRuZXByLnB5IiwgIk5ldyBUYWkgTHVlIjogImxheW91dF9LQkROVEwucHkiLCAiTm9yd2VnaWFuIjogImxheW91dF9LQkROTy5weSIsICJOb3J3ZWdpYW4gd2l0aCBTYW1pIjogImxheW91dF9rYmRubzEucHkiLCAiT2RpYSI6ICJsYXlvdXRfS0JESU5PUkkucHkiLCAiT2doYW0iOiAibGF5b3V0X0tCRE9HSEFNLnB5IiwgIk9sIENoaWtpIjogImxheW91dF9LQkRPTENILnB5IiwgIk9sZCBJdGFsaWMiOiAibGF5b3V0X0tCRE9MRElULnB5IiwgIk9zYWdlIjogImxheW91dF9LQkRPU0EucHkiLCAiT3NtYW55YSI6ICJsYXlvdXRfS0JET1NNLnB5IiwgIlBhc2h0byAoQWZnaGFuaXN0YW4pIjogImxheW91dF9rYmRwYXNoLnB5IiwgIlBlcnNpYW4iOiAibGF5b3V0X0tCREZBLnB5IiwgIlBlcnNpYW4gKFN0YW5kYXJkKSI6ICJsYXlvdXRfa2JkZmFyLnB5IiwgIlBoYWdzLXBhIjogImxheW91dF9rYmRwaGFncy5weSIsICJQb2xpc2ggKDIxNCkiOiAibGF5b3V0X0tCRFBMLnB5IiwgIlBvbGlzaCAoUHJvZ3JhbW1lcnMpIjogImxheW91dF9LQkRQTDEucHkiLCAiUG9ydHVndWVzZSI6ICJsYXlvdXRfS0JEUE8ucHkiLCAiUG9ydHVndWVzZSAoQnJhemlsIEFCTlQpIjogImxheW91dF9LQkRCUi5weSIsICJQb3J0dWd1ZXNlIChCcmF6aWwgQUJOVDIpIjogImxheW91dF9LQkRCUi5weSIsICJQdW5qYWJpIjogImxheW91dF9LQkRJTlBVTi5weSIsICJSb21hbmlhbiAoTGVnYWN5KSI6ICJsYXlvdXRfS0JEUk8ucHkiLCAiUm9tYW5pYW4gKFByb2dyYW1tZXJzKSI6ICJsYXlvdXRfS0JEUk9QUi5weSIsICJSb21hbmlhbiAoU3RhbmRhcmQpIjogImxheW91dF9LQkRST1NULnB5IiwgIlJ1c3NpYW4iOiAibGF5b3V0X0tCRFJVLnB5IiwgIlJ1c3NpYW4gLSBNbmVtb25pYyI6ICJsYXlvdXRfS0JEUlVNLnB5IiwgIlJ1c3NpYW4gKFR5cGV3cml0ZXIpIjogImxheW91dF9LQkRSVTEucHkiLCAiU2FraGEiOiAibGF5b3V0X0tCRFlBSy5weSIsICJTYW1pIEV4dGVuZGVkIEZpbmxhbmQtU3dlZGVuIjogImxheW91dF9rYmRzbXNmaS5weSIsICJTYW1pIEV4dGVuZGVkIE5vcndheSI6ICJsYXlvdXRfa2Jkc21zbm8ucHkiLCAiU2NvdHRpc2ggR2FlbGljIjogImxheW91dF9LQkRHQUUucHkiLCAiU2VyYmlhbiAoQ3lyaWxsaWMpIjogImxheW91dF9LQkRZQ0MucHkiLCAiU2VyYmlhbiAoTGF0aW4pIjogImxheW91dF9LQkRZQ0wucHkiLCAiU2V0c3dhbmEiOiAibGF5b3V0X0tCRE5TTy5weSIsICJTZXNvdGhvIHNhIExlYm9hIjogImxheW91dF9LQkROU08ucHkiLCAiU2luaGFsYSI6ICJsYXlvdXRfS0JEU04xLnB5IiwgIlNpbmhhbGEgLSBXaWogOSI6ICJsYXlvdXRfS0JEU1cwOS5weSIsICJTbG92YWsiOiAibGF5b3V0X0tCRFNMLnB5IiwgIlNsb3ZhayAoUVdFUlRZKSI6ICJsYXlvdXRfS0JEU0wxLnB5IiwgIlN0YW5kYXJkIjogImxheW91dF9LQkRDUi5weSIsICJTbG92ZW5pYW4iOiAibGF5b3V0X0tCRENSLnB5IiwgIlNvcmEiOiAibGF5b3V0X0tCRFNPUkEucHkiLCAiU29yYmlhbiBFeHRlbmRlZCI6ICJsYXlvdXRfS0JEU09SRVgucHkiLCAiU29yYmlhbiBTdGFuZGFyZCI6ICJsYXlvdXRfS0JEU09SUzEucHkiLCAiU29yYmlhbiBTdGFuZGFyZCAoTGVnYWN5KSI6ICJsYXlvdXRfS0JEU09SU1QucHkiLCAiU3BhbmlzaCI6ICJsYXlvdXRfS0JEU1AucHkiLCAiU3BhbmlzaCBWYXJpYXRpb24iOiAibGF5b3V0X0tCREVTLnB5IiwgIlN3ZWRpc2giOiAibGF5b3V0X0tCRFNXLnB5IiwgIlN3aXNzIEdlcm1hbiI6ICJsYXlvdXRfS0JEU0cucHkiLCAiU3lyaWFjIjogImxheW91dF9LQkRTWVIxLnB5IiwgIlN5cmlhYyBQaG9uZXRpYyI6ICJsYXlvdXRfS0JEU1lSMi5weSIsICJUYWkgTGUiOiAibGF5b3V0X0tCRFRBSUxFLnB5IiwgIlRhamlrIjogImxheW91dF9LQkRUQUpJSy5weSIsICJUYW1pbCI6ICJsYXlvdXRfS0JESU5UQU0ucHkiLCAiVGFtaWwgOTkiOiAibGF5b3V0X0tCRFRBTTk5LnB5IiwgIlRhdGFyIjogImxheW91dF9LQkRUVDEwMi5weSIsICJUYXRhciAoTGVnYWN5KSI6ICJsYXlvdXRfS0JEVEFULnB5IiwgIlRlbHVndSI6ICJsYXlvdXRfS0JESU5URUwucHkiLCAiVGhhaSBLZWRtYW5lZSI6ICJsYXlvdXRfS0JEVEgwLnB5IiwgIlRoYWkgS2VkbWFuZWUgKG5vbi1TaGlmdExvY2spIjogImxheW91dF9LQkRUSDIucHkiLCAiVGhhaSBQYXR0YWNob3RlIjogImxheW91dF9LQkRUSDEucHkiLCAiVGhhaSBQYXR0YWNob3RlIChub24tU2hpZnRMb2NrKSI6ICJsYXlvdXRfS0JEVEgzLnB5IiwgIlRpYmV0YW4gKFBSQykiOiAibGF5b3V0X0tCRFRJUFJDLnB5IiwgIlRpYmV0YW4gKFBSQykgLSBVcGRhdGVkIjogImxheW91dF9LQkRUSVBSRC5weSIsICJUaWZpbmFnaCAoQmFzaWMpIjogImxheW91dF9LQkRUSUZJLnB5IiwgIlRpZmluYWdoIChFeHRlbmRlZCkiOiAibGF5b3V0X0tCRFRJRkkyLnB5IiwgIlRyYWRpdGlvbmFsIE1vbmdvbGlhbiAoU3RhbmRhcmQpIjogImxheW91dF9LQkRNT05TVC5weSIsICJUdXJraXNoIEYiOiAibGF5b3V0X0tCRFRVRi5weSIsICJUdXJraXNoIFEiOiAibGF5b3V0X0tCRFRVUS5weSIsICJUdXJrbWVuIjogImxheW91dF9LQkRUVVJNRS5weSIsICJVa3JhaW5pYW4iOiAibGF5b3V0X0tCRFVSLnB5IiwgIlVrcmFpbmlhbiAoRW5oYW5jZWQpIjogImxheW91dF9LQkRVUjEucHkiLCAiVW5pdGVkIEtpbmdkb20iOiAibGF5b3V0X0tCRFVLLnB5IiwgIlVuaXRlZCBLaW5nZG9tIEV4dGVuZGVkIjogImxheW91dF9rYmR1a3gucHkiLCAiVW5pdGVkIFN0YXRlcy1Edm9yYWsiOiAibGF5b3V0X0tCRERWLnB5IiwgIlVuaXRlZCBTdGF0ZXMtRHZvcmFrIGZvciBsZWZ0IGhhbmQiOiAibGF5b3V0X0tCRFVTTC5weSIsICJVbml0ZWQgU3RhdGVzLUR2b3JhayBmb3IgcmlnaHQgaGFuZCI6ICJsYXlvdXRfS0JEVVNSLnB5IiwgIlVuaXRlZCBTdGF0ZXMtSW50ZXJuYXRpb25hbCI6ICJsYXlvdXRfS0JEVVNYLnB5IiwgIlVyZHUiOiAibGF5b3V0X0tCRFVSRFUucHkiLCAiVVMgRW5nbGlzaCBUYWJsZSBmb3IgSUJNIEFyYWJpYyAyMzhfTCI6ICJsYXlvdXRfS0JEVVNBLnB5IiwgIlV5Z2h1ciI6ICJsYXlvdXRfS0JEVUdIUjEucHkiLCAiVXlnaHVyIChMZWdhY3kpIjogImxheW91dF9LQkRVR0hSLnB5IiwgIlV6YmVrIEN5cmlsbGljIjogImxheW91dF9LQkRVWkIucHkiLCAiVmlldG5hbWVzZSI6ICJsYXlvdXRfS0JEVk5UQy5weSIsICJXb2xvZiI6ICJsYXlvdXRfS0JEV09MLnB5IiwgIllvcnViYSI6ICJsYXlvdXRfS0JEWUJBLnB5IiwgIkRFQyBMSzQxMS1BSiBLZXlib2FyZCBMYXlvdXQiOiAibGF5b3V0X2tiZGxrNDFhLnB5IiwgIkpQIEphcGFuZXNlIEtleWJvYXJkIExheW91dCBmb3IgKE5FQyBQQy05ODAwIG9uIFBDOTgtTlgpIjogImxheW91dF9rYmRuZWNhdC5weSIsICJKUCBKYXBhbmVzZSBLZXlib2FyZCBMYXlvdXQgZm9yIChORUMgUEMtOTgwMCBXaW5kb3dzIDk1KSI6ICJsYXlvdXRfa2JkbmVjOTUucHkiLCAiSlAgSmFwYW5lc2UgS2V5Ym9hcmQgTGF5b3V0IGZvciAoTkVDIFBDLTk4MDApIjogImxheW91dF9rYmRuZWMucHkiLCAiSlAgSmFwYW5lc2UgS2V5Ym9hcmQgTGF5b3V0IGZvciAxMDEiOiAibGF5b3V0X2tiZDEwMS5weSIsICJKUCBKYXBhbmVzZSBLZXlib2FyZCBMYXlvdXQgZm9yIDEwNiI6ICJsYXlvdXRfa2JkMTA2LnB5IiwgIkpQIEphcGFuZXNlIEtleWJvYXJkIExheW91dCBmb3IgQVgyIjogImxheW91dF9rYmRheDIucHkiLCAiSlAgSmFwYW5lc2UgS2V5Ym9hcmQgTGF5b3V0IGZvciBJQk0gNTU3Ni0wMDIvMDAzIjogImxheW91dF9rYmRpYm0wMi5weSIsICJKUCBKYXBhbmVzZSBORUMgUEMtOTgwMCBLZXlib2FyZCBMYXlvdXQiOiAibGF5b3V0X2tiZG5lY250LnB5IiwgIktPIEhhbmdldWwgS2V5Ym9hcmQgTGF5b3V0IGZvciAxMDEgKFR5cGUgQSkiOiAibGF5b3V0X2tiZDEwMWEucHkiLCAiS08gSGFuZ2V1bCBLZXlib2FyZCBMYXlvdXQgZm9yIDEwMShUeXBlIEIpIjogImxheW91dF9rYmQxMDFiLnB5IiwgIktPIEhhbmdldWwgS2V5Ym9hcmQgTGF5b3V0IGZvciAxMDEoVHlwZSBDKSI6ICJsYXlvdXRfa2JkMTAxYy5weSIsICJLTyBIYW5nZXVsIEtleWJvYXJkIExheW91dCBmb3IgMTAzIjogImxheW91dF9rYmQxMDMucHkifQ==").decode())
        self.shortnames_to_filename = json.loads(base64.b64decode("eyJmZmFkbG0iOiAibGF5b3V0X0tCREFETE0ucHkiLCAic3EiOiAibGF5b3V0X0tCREFMLnB5IiwgImFyc2EiOiAibGF5b3V0X0tCREEzLnB5IiwgImh5IjogImxheW91dF9LQkRBUk1XLnB5IiwgImFzIjogImxheW91dF9LQkRJTkFTQS5weSIsICJhemxhdG4iOiAibGF5b3V0X0tCREFaRUwucHkiLCAiYXpjeXJsIjogImxheW91dF9LQkRBWkUucHkiLCAiYm5pbiI6ICJsYXlvdXRfa2JkaW5iZW4ucHkiLCAiYmFjeXJsIjogImxheW91dF9LQkRCQVNILnB5IiwgImJlIjogImxheW91dF9LQkRCTFIucHkiLCAiZnJiZSI6ICJsYXlvdXRfS0JEQkUucHkiLCAibmxiZSI6ICJsYXlvdXRfS0JEQkUucHkiLCAiYnNjeXJsIjogImxheW91dF9rYmRiaGMucHkiLCAiYnVnYnVnaSI6ICJsYXlvdXRfS0JEQlVHLnB5IiwgImJnIjogImxheW91dF9LQkRVUy5weSIsICJ6aGhhbnR0dyI6ICJsYXlvdXRfS0JEVVMucHkiLCAiZW51cyI6ICJsYXlvdXRfS0JEVVNYLnB5IiwgInpoaGFuc2NuIjogImxheW91dF9LQkRVUy5weSIsICJ6aGhhbnRoayI6ICJsYXlvdXRfS0JEVVMucHkiLCAiemhoYW5zc2ciOiAibGF5b3V0X0tCRFVTLnB5IiwgInpoaGFudG1vIjogImxheW91dF9LQkRVUy5weSIsICJlbmNhIjogImxheW91dF9LQkRDQU4ucHkiLCAiZnJjYSI6ICJsYXlvdXRfS0JERkMucHkiLCAidHptbGF0biI6ICJsYXlvdXRfS0JEVFpNLnB5IiwgImt1YXJhYiI6ICJsYXlvdXRfS0JES1VSRC5weSIsICJjcyI6ICJsYXlvdXRfS0JEQ1oyLnB5IiwgImNocmNoZXIiOiAibGF5b3V0X0tCRENIRVJQLnB5IiwgImRhIjogImxheW91dF9LQkREQS5weSIsICJoaSI6ICJsYXlvdXRfS0JESU5ISU4ucHkiLCAiZHYiOiAibGF5b3V0X0tCRERJVjIucHkiLCAibmxubCI6ICJsYXlvdXRfa2JkbmUucHkiLCAiZHoiOiAibGF5b3V0X0tCRERaTy5weSIsICJlbmluIjogImxheW91dF9LQkRJTkVOLnB5IiwgImV0IjogImxheW91dF9LQkRFU1QucHkiLCAiZm8iOiAibGF5b3V0X0tCREZPLnB5IiwgImZpIjogImxheW91dF9LQkRGSS5weSIsICJzZWxhdG5zZSI6ICJsYXlvdXRfa2Jkc21zZmkucHkiLCAiZnJmciI6ICJsYXlvdXRfS0JERlIucHkiLCAiZ2VtcnVuciI6ICJsYXlvdXRfS0JERlRIUksucHkiLCAia2EiOiAibGF5b3V0X0tCREdFTy5weSIsICJkZWRlIjogImxheW91dF9LQkRHUjEucHkiLCAiZ290Z290aCI6ICJsYXlvdXRfS0JER1RIQy5weSIsICJlbCI6ICJsYXlvdXRfS0JESEVQVC5weSIsICJrbCI6ICJsYXlvdXRfS0JER1JMTkQucHkiLCAiZ24iOiAibGF5b3V0X0tCREdOLnB5IiwgImd1IjogImxheW91dF9LQkRJTkdVSi5weSIsICJoYWxhdG4iOiAibGF5b3V0X0tCREhBVS5weSIsICJoYXdsYXRuIjogImxheW91dF9LQkRIQVcucHkiLCAiaGUiOiAibGF5b3V0X0tCREhFQi5weSIsICJodSI6ICJsYXlvdXRfS0JESFUucHkiLCAiaXMiOiAibGF5b3V0X0tCRElDLnB5IiwgImlnbGF0biI6ICJsYXlvdXRfS0JESUJPLnB5IiwgIml1bGF0biI6ICJsYXlvdXRfS0JESVVMQVQucHkiLCAiaXVjYW5zIjogImxheW91dF9LQkRJTlVLMi5weSIsICJlbmllIjogImxheW91dF9LQkRHQUUucHkiLCAiaXRpdCI6ICJsYXlvdXRfS0JESVQucHkiLCAiamEiOiAibGF5b3V0X0tCREpQTi5weSIsICJqdmphdmEiOiAibGF5b3V0X0tCREpBVi5weSIsICJrbiI6ICJsYXlvdXRfS0JESU5LQU4ucHkiLCAia2siOiAibGF5b3V0X0tCREtBWi5weSIsICJrbSI6ICJsYXlvdXRfS0JES05JLnB5IiwgImtvIjogImxheW91dF9LQkRLT1IucHkiLCAia3ljeXJsIjogImxheW91dF9LQkRLWVIucHkiLCAibG8iOiAibGF5b3V0X0tCRExBTy5weSIsICJlc214IjogImxheW91dF9LQkRMQS5weSIsICJsdiI6ICJsYXlvdXRfS0JETFYxLnB5IiwgImxpc2xpc3UiOiAibGF5b3V0X2tiZGxpc3VzLnB5IiwgImx0IjogImxheW91dF9LQkRMVDIucHkiLCAibGIiOiAibGF5b3V0X0tCRFNGLnB5IiwgImZyY2giOiAibGF5b3V0X0tCRFNGLnB5IiwgIm1rIjogImxheW91dF9LQkRNQUMucHkiLCAibWwiOiAibGF5b3V0X2tiZGlubWFsLnB5IiwgIm10IjogImxheW91dF9rYmRtbHQ0OC5weSIsICJtaWxhdG4iOiAibGF5b3V0X2tiZG1hb3JpLnB5IiwgImVubnoiOiAibGF5b3V0X2tiZG1hb3JpLnB5IiwgIm1yIjogImxheW91dF9LQkRJTk1BUi5weSIsICJtbm1vbmciOiAibGF5b3V0X0tCRE1PTlNULnB5IiwgIm1uY3lybCI6ICJsYXlvdXRfS0JETU9OLnB5IiwgIm15IjogImxheW91dF9LQkRNWUFOLnB5IiwgIm5xbyI6ICJsYXlvdXRfa2JkbmtvLnB5IiwgIm5lbnAiOiAibGF5b3V0X2tiZG5lcHIucHkiLCAia2hidGFsdSI6ICJsYXlvdXRfS0JETlRMLnB5IiwgIm5iIjogImxheW91dF9LQkROTy5weSIsICJzZWxhdG5ubyI6ICJsYXlvdXRfa2Jkc21zbm8ucHkiLCAib3IiOiAibGF5b3V0X0tCRElOT1JJLnB5IiwgInNnYW9nYW0iOiAibGF5b3V0X0tCRE9HSEFNLnB5IiwgInNhdG9sY2siOiAibGF5b3V0X0tCRE9MQ0gucHkiLCAiZXR0aXRhbCI6ICJsYXlvdXRfS0JET0xESVQucHkiLCAib3Nhb3NnZSI6ICJsYXlvdXRfS0JET1NBLnB5IiwgInNvb3NtYSI6ICJsYXlvdXRfS0JET1NNLnB5IiwgInBzIjogImxheW91dF9rYmRwYXNoLnB5IiwgImZhIjogImxheW91dF9rYmRmYXIucHkiLCAibW5waGFnIjogImxheW91dF9rYmRwaGFncy5weSIsICJwbCI6ICJsYXlvdXRfS0JEUEwxLnB5IiwgInB0cHQiOiAibGF5b3V0X0tCRFBPLnB5IiwgInB0YnIiOiAibGF5b3V0X0tCREJSLnB5IiwgInBhIjogImxheW91dF9LQkRJTlBVTi5weSIsICJyb3JvIjogImxheW91dF9LQkRST1NULnB5IiwgInJ1IjogImxheW91dF9LQkRSVS5weSIsICJzYWhjeXJsIjogImxheW91dF9LQkRZQUsucHkiLCAic3JjeXJsY3MiOiAibGF5b3V0X0tCRFlDQy5weSIsICJzcmxhdG5jcyI6ICJsYXlvdXRfS0JEWUNMLnB5IiwgInRuemEiOiAibGF5b3V0X0tCRE5TTy5weSIsICJuc28iOiAibGF5b3V0X0tCRE5TTy5weSIsICJzaSI6ICJsYXlvdXRfS0JEU04xLnB5IiwgInNrIjogImxheW91dF9LQkRTTDEucHkiLCAiaHJociI6ICJsYXlvdXRfS0JEQ1IucHkiLCAic2wiOiAibGF5b3V0X0tCRENSLnB5IiwgInNyYnNvcmEiOiAibGF5b3V0X0tCRFNPUkEucHkiLCAiaHNiIjogImxheW91dF9LQkRTT1JTMS5weSIsICJlc2VzIjogImxheW91dF9LQkRTUC5weSIsICJzdnNlIjogImxheW91dF9LQkRTVy5weSIsICJkZWNoIjogImxheW91dF9LQkRTRy5weSIsICJzeXJzeXJjIjogImxheW91dF9LQkRTWVIxLnB5IiwgInRkZHRhbGUiOiAibGF5b3V0X0tCRFRBSUxFLnB5IiwgInRnY3lybCI6ICJsYXlvdXRfS0JEVEFKSUsucHkiLCAidGFpbiI6ICJsYXlvdXRfS0JEVEFNOTkucHkiLCAidHRjeXJsIjogImxheW91dF9LQkRUVDEwMi5weSIsICJ0ZSI6ICJsYXlvdXRfS0JESU5URUwucHkiLCAidGgiOiAibGF5b3V0X0tCRFRIMS5weSIsICJib3RpYnQiOiAibGF5b3V0X0tCRFRJUFJDLnB5IiwgInR6bXRmbmciOiAibGF5b3V0X0tCRFRJRkkyLnB5IiwgInRyIjogImxheW91dF9LQkRUVVEucHkiLCAidGtsYXRuIjogImxheW91dF9LQkRUVVJNRS5weSIsICJ1ayI6ICJsYXlvdXRfS0JEVVIucHkiLCAiZW5nYiI6ICJsYXlvdXRfS0JEVUsucHkiLCAiY3kiOiAibGF5b3V0X2tiZHVreC5weSIsICJ1cnBrIjogImxheW91dF9LQkRVUkRVLnB5IiwgInVnYXJhYiI6ICJsYXlvdXRfS0JEVUdIUjEucHkiLCAidXpjeXJsIjogImxheW91dF9LQkRVWkIucHkiLCAidmkiOiAibGF5b3V0X0tCRFZOVEMucHkiLCAid29sYXRuIjogImxheW91dF9LQkRXT0wucHkiLCAieW9sYXRuIjogImxheW91dF9LQkRZQkEucHkifQ==").decode())
    
    def __layout_loader(self, filename):
        layoutdata = importlib.import_module('aardwolf.keyboard.layouts.%s' % filename[:-3])
        return KeyboardLayout.from_layoutdata(layoutdata.layoutdata)


    def get_layout_by_klid(self, klid):
        if klid not in self.klids_to_filename:
            return None
        return self.__layout_loader(self.klids_to_filename[klid])

    def get_layout_by_name(self, name):
        if name not in self.names_to_filename:
            return None
        
        return self.__layout_loader(self.names_to_filename[name]) 
    
    def get_layout_by_shortname(self, name):
        if name not in self.shortnames_to_filename:
            return None
        return self.__layout_loader(self.shortnames_to_filename[name]) 
    
    def get_klids(self):
        for klid in self.klids_to_filename:
            yield klid
    
    def get_names(self):
        for name in self.names_to_filename:
            yield name
    
    def get_shortnames(self):
        for name in self.shortnames_to_filename:
            yield name

if __name__ == '__main__':
    kl = KeyboardLayoutManager()
    kl.get_layout_by_shorname('sq')