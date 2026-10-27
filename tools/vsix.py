"""Bundle the owned VS Code companion without npm build dependencies."""
from .archive import zip_bytes

MANIFEST = '''<?xml version="1.0" encoding="utf-8"?>
<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011">
 <Metadata><Identity Language="en-US" Id="claude-sidebar-bridge" Version="0.1.0" Publisher="kaizen-local"/>
 <DisplayName>Kaizen Claude Sidebar Bridge</DisplayName>
 <Description xml:space="preserve">Local sidebar routing</Description>
 <Tags/><Categories>Other</Categories><GalleryFlags>Public</GalleryFlags>
 <Properties><Property Id="Microsoft.VisualStudio.Code.Engine" Value="^1.94.0"/></Properties></Metadata>
 <Installation><InstallationTarget Id="Microsoft.VisualStudio.Code"/></Installation><Dependencies/>
 <Assets><Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true"/></Assets>
</PackageManifest>'''

TYPES = '''<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="json" ContentType="application/json"/><Default Extension="js" ContentType="application/javascript"/>
<Default Extension="vsixmanifest" ContentType="text/xml"/><Default Extension="txt" ContentType="text/plain"/></Types>'''

def companion(maintained):
    files = {'extension.vsixmanifest': MANIFEST.encode(), '[Content_Types].xml': TYPES.encode()}
    for name, data in maintained.items():
        if name.startswith('sidebar_companion/'):
            files['extension/' + name.split('/', 1)[1]] = data
    files['extension/LICENSE.txt'] = maintained['LICENSE']
    files['extension/NOTICE.txt'] = maintained['NOTICE']
    return zip_bytes(files)
