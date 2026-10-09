import unittest
from datetime import datetime, timezone
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from generate import API, collect, month_keys, svg


class FakeAPI:
    def pages(self, path):
        if '/users/' in path:
            return [dict(name=name, owner={'login':'jburn'}, private=private, fork=fork, size=1, stargazers_count=2, description='A tool', html_url='https://github.com/jburn/'+name, language='Python') for name,private,fork in [('a',False,False),('b',False,False),('fork',False,True),('secret',True,False),('skip',False,False)]]
        return [{'sha':'same', 'author':{'login':'jburn'}, 'commit':{'committer':{'date':'2026-10-01T12:00:00Z'}}}, {'sha':'other', 'author':None, 'commit':{'committer':{'date':'2026-10-01T12:00:00Z'}}}]

    def get(self, path):
        return {'Python':300, 'JavaScript':100}, ''


class Tests(unittest.TestCase):
    def test_calculations_and_privacy(self):
        result=collect({'username':'jburn','exclude_repositories':['skip'],'exclude_forks':True,'featured':['a']}, datetime(2026,10,9,tzinfo=timezone.utc), FakeAPI())
        self.assertEqual(result['public_repositories'],4)
        self.assertEqual(result['included_repositories'],2)
        self.assertEqual(result['stars'],4)
        self.assertEqual(result['languages'],{'Python':600,'JavaScript':200})
        self.assertEqual(result['commits'],1)
        self.assertEqual(result['active_days'],1)
        self.assertEqual(result['monthly_commits']['2026-10'],1)
        self.assertEqual(result['window_start'],'2025-11-01')
        self.assertEqual(len(result['projects']),1)

    def test_year_boundary(self):
        keys=month_keys(datetime(2026,1,1))
        self.assertEqual(keys[0],'2025-02')
        self.assertEqual(keys[-1],'2026-01')
        self.assertEqual(len(keys),12)

    def test_pagination(self):
        class Pages(API):
            def get(self,path):
                return ([1], '<https://api.github.com/next>; rel="next"') if path=='/first' else ([2], '')
        self.assertEqual(Pages().pages('/first'),[1,2])

    def test_failure_is_not_zero(self):
        class Broken(FakeAPI):
            def get(self,path): raise RuntimeError('Unavailable')
        with self.assertRaises(RuntimeError):
            collect({'username':'jburn','exclude_repositories':[],'exclude_forks':True,'featured':[]},datetime(2026,10,9,tzinfo=timezone.utc),Broken())

    def test_safe_svg(self):
        root=ET.fromstring(svg(100,100,'A & B',''))
        self.assertEqual(root.find('{http://www.w3.org/2000/svg}title').text,'A & B')
        for path in (Path(__file__).resolve().parents[1]/'assets/generated').glob('*.svg'):
            root=ET.parse(path).getroot()
            self.assertTrue(root.get('viewBox'))
            for element in root.iter():
                self.assertNotIn(element.tag.rsplit('}',1)[-1], ['script','foreignObject','image'])
                self.assertFalse(any(key.startswith('on') for key in element.attrib))


if __name__=='__main__': unittest.main()
