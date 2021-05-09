# Automated Jinja SSTI exploit tool
Uses simple straight strategy to get code execution on vulnerable system

Provide file containing raw HTTP request with `<ssti>` mark in the vulnerable parameter as argument

```bash
python3 ajssti.py -r req.txt
```

## To implement:
 - [ ] HTTPS support
 - [ ] Badchar filtering bypasses
 - [ ] Another strategies to get rce or file read
