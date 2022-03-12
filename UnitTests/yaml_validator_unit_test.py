import unittest
import os
import gitlabbot


class YamlTest(unittest.TestCase):

    def testCorrectYaml(self):
        with open("YamlSamples/CorrectYaml.yml", "r", encoding="utf-8") as yaml_str:
            yaml_valid = gitlabbot.YamlValidator(yaml_str.read())
            results = yaml_valid.validate_yaml()
            self.assertTrue(results.success)

    def testMissingRequired(self):
        with os.scandir("YamlSamples") as yaml_files:
            for entry in yaml_files:
                if(entry.name.find("Missing") != -1):
                    with open("YamlSamples/"+entry.name, "r", encoding="utf-8") as yaml_file:
                        print("Testing "+entry.name)
                        yaml_valid = gitlabbot.YamlValidator(yaml_file.read())
                        results = yaml_valid.validate_yaml()
                        self.assertFalse(results.success)


if __name__ == '__main__':
    unittest.main()
