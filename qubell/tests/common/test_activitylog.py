import unittest
from qubell.api.private.instance import activityLog

class test_activityLog(unittest.TestCase):
    actlog = [{"time": 1402654329064, "description": "Status is Destroyed", "severity": "INFO"},
              {"time": 1402654329000, "description": "Job destroy (destroy) finished", "severity": "INFO"},
              {"time": 1402654291529, "description": "Status is Executing", "severity": "DEBUG"},
              {"time": 1402654291390,
               "description": "Signals updated:\nendpoints.entry: http://54.89.221.226",
               "severity": "DEBUG"},
              {"time": 1402654291342, "description": "Status is Unknown", "severity": "WARNING"},
              {"time": 1402654291000, "description": "Job destroy (539ace53e4b036d47b68094f) started",
               "userInfo": {"id": "515d6184e4b052964c25c668", "email": "tester@yandex.com",
                            "fullName": "Tester"}, "severity": "INFO"},
              {"time": 1402653907198, "description": "Status is Running", "severity": "INFO"},
              {"time": 1402653907146,
               "description": "Component 'main.workflow' finished workflow 'app-scale' with status Succeeded",
               "severity": "INFO"},
              {"time": 1402653906934, "description": "Component 'main.workflow' finished step: lb-reconfigure-servers",
               "severity": "DEBUG"},
              {"time": 1402653906006,
               "description": "Component 'lb.workflow' finished workflow 'reconfigure-servers' with status Succeeded",
               "severity": "INFO"},
              {"time": 1402653905756, "description": "Component 'lb.workflow' finished step: reconfigure-servers",
               "severity": "DEBUG"},
              {"time": 1402653884661, "description": "Component 'lb.workflow' started step: reconfigure-servers",
               "severity": "DEBUG"},
              {"time": 1402653884595,
               "description": "Dynamic links updated on component 'lb.workflow':\napp-hosts:\n- 54.89.216.129\n- 54.89.68.110",
               "severity": "DEBUG"},
              {"time": 1402653884517, "description": "Component 'lb.workflow' started workflow: reconfigure-servers",
               "severity": "INFO"},
              {"time": 1402653884310, "description": "Component 'main.workflow' started step: lb-reconfigure-servers",
               "severity": "DEBUG"},
              {"time": 1402653884029, "description": "Component 'main.workflow' finished step: deploy-war",
               "severity": "DEBUG"},
              {"time": 1402653883483,
               "description": "Component 'app.workflow' finished workflow 'deploy-war' with status Succeeded",
               "severity": "INFO"},
              {"time": 1402653882995, "description": "Component 'app.workflow' finished step: deploy-war",
               "severity": "DEBUG"},
              {"time": 1402653846969, "description": "Component 'app.workflow' started step: deploy-war",
               "severity": "DEBUG"},
              {"time": 1402653846736, "description": "Component 'app.workflow' started workflow: deploy-war",
               "severity": "INFO"},
              {"time": 1402653846109, "description": "Component 'main.workflow' started step: deploy-war",
               "severity": "DEBUG"},
              {"time": 1402653845850, "description": "Component 'main.workflow' finished step: deploy-libs",
               "severity": "DEBUG"},
              {"time": 1402653845840, "description": "Reconfiguration requested: input.app-quantity: '2'",
               "userInfo": {"id": "515d6184e4b052964c25c668", "email": "tester@yandex.com",
                                "fullName": "Tester Cometera"}, "severity": "INFO"},
              {"time": 1402653845830, "description": "Status is Running", "severity": "INFO"},
              {"time": 1402653845820, "description": "Job launch (launch) finished", "severity": "INFO"},
              {"time": 1402653845810
                  ,
               "description": "Component 'app.workflow' finished workflow 'deploy-libs' with status Succeeded",
               "severity": "INFO"},
              {"time": 1402653844795, "description": "Component 'app.workflow' finished step: deploy-libs",
               "severity": "DEBUG"},
              {"time": 1402653816369, "description": "Component 'app.workflow' started step: deploy-libs",
               "severity": "DEBUG"},
              {"time": 1402653816323, "description": "Component 'app.workflow' started workflow: deploy-libs",
               "severity": "INFO"},
              {"time": 1402653816236, "description": "Component 'main.workflow' started step: deploy-libs",
               "severity": "DEBUG"},
              {"time": 1402651965000, "description": "Job launch (539ac53de4b036d47b6807a1) started",
               "userInfo": {"id": "515d6184e4b052964c25c668", "email": "aaa@aaa.aaa", "fullName": "Tester"},
               "severity": "INFO"}]

    def test_sugar(self):
        all_logs = activityLog(self.actlog)
        info_logs = activityLog(self.actlog, severity='INFO')

        self.assertEqual(len(all_logs), 31)
        self.assertEqual(len(info_logs), 15)

        for log in info_logs:
            assert log['severity'] == 'INFO'

        assert 'Status is Running' in info_logs
        self.assertEqual(all_logs['Job launch \(.*\) started'], 1402651965000)
        self.assertEqual(all_logs['Job launch \(539ac53de4b036d47b6807a1\) started'], 1402651965000)
        self.assertEqual(all_logs[1402651965000], 'Job launch (539ac53de4b036d47b6807a1) started')
        self.assertEqual(all_logs[0], 'Job launch (539ac53de4b036d47b6807a1) started')
        self.assertEqual(all_logs[-1], 'Status is Destroyed')


    def test_interval_start(self):
        logs = activityLog(self.actlog, severity='INFO', start=1402653845840)
        self.assertEqual(len(logs), 10)
        self.assertEqual(logs[0], "Reconfiguration requested: input.app-quantity: '2'")
        self.assertEqual(logs[-1], "Status is Destroyed")

    def test_interval_end(self):
        logs = activityLog(self.actlog, severity='INFO', end=1402653907198)
        self.assertEqual(len(logs), 12)
        self.assertEqual(logs[0], "Job launch (539ac53de4b036d47b6807a1) started")
        self.assertEqual(logs[-1], "Status is Running")

    def test_get_interval(self):
        logs = activityLog(self.actlog, severity='INFO').get_interval("Job launch \(539ac53de4b036d47b6807a1\) started", "Job launch \(launch\) finished")
        self.assertEqual(len(logs), 4)
        self.assertEqual(logs[0], "Job launch (539ac53de4b036d47b6807a1) started")
        self.assertEqual(logs[-1], "Job launch (launch) finished")

        logs = activityLog(self.actlog, severity='INFO').get_interval("Job launch \(539ac53de4b036d47b6807a1\) started")
        self.assertEqual(len(logs), 15)

        logs = activityLog(self.actlog, severity='INFO').get_interval(end_text="Job launch \(launch\) finished")
        self.assertEqual(len(logs), 4)
