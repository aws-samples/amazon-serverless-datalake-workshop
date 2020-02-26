# Editing the workshop


In order for changes in the instructions.md to propgrate to the lab, you need to convert the instructions into the instuctions-template.html.

To do this, install grip to perform the conversion. For more information on Grip, go to: https://github.com/joeyespo/grip

```
pip install grip
```

To preview your changes, run grip on the command line:
```
grip instructions.md
```

The command line will tell you the port on localhost to use to view the document. Keep in mind, the tokens will still appear in the document such as ^ingestionbucket^.

To create the html document, run the export function

```
grip instructions.md --export instructions-template.html
```