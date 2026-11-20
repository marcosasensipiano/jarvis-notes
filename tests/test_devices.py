import unittest
from unittest import mock

from jarvis.devices import network, tv


class Net(unittest.TestCase):
    def test_parse_ssdp(self):
        raw = b"HTTP/1.1 200 OK\r\nSERVER: Roku/9.4 UPnP/1.0\r\nLOCATION: http://192.168.1.50:8060/\r\nST: roku:ecp\r\n\r\n"
        h = network.parse_ssdp(raw)
        self.assertEqual(h["location"], "http://192.168.1.50:8060/")
        self.assertEqual(network.classify(" ".join(h.values())), "roku")
        self.assertEqual(network.classify("Linux UPnP/1.0 webOS"), "lg")
        self.assertEqual(network.classify("nothing"), "unknown")

    def test_parse_neighbors(self):
        ip = "192.168.1.7 dev wlan0 lladdr aa:bb:cc:dd:ee:ff REACHABLE\n10.0.0.2 dev wlan0  FAILED"
        self.assertEqual(network.parse_neighbors(ip), {"192.168.1.7": "aa:bb:cc:dd:ee:ff"})
        arp = "? (192.168.1.9) at aa:bb:cc:dd:ee:01 on en0 ifscope [ethernet]"
        self.assertEqual(network.parse_neighbors(arp), {"192.168.1.9": "aa:bb:cc:dd:ee:01"})


class TV(unittest.TestCase):
    def test_roku_request(self):
        with mock.patch("urllib.request.urlopen") as op:
            r = tv.RokuTV("1.2.3.4").send("volume_up")
        req = op.call_args[0][0]
        self.assertEqual(req.full_url, "http://1.2.3.4:8060/keypress/VolumeUp")
        self.assertEqual(req.get_method(), "POST")
        self.assertEqual(r, "Roku: volume_up")

    def test_roku_unreachable_is_a_message_not_a_crash(self):
        with mock.patch("urllib.request.urlopen", side_effect=OSError("boom")):
            self.assertIn("didn't answer", tv.RokuTV("1.2.3.4").send("home"))

    def test_adb_keycodes(self):
        a = tv.AdbTV("1.2.3.4")
        calls = []
        with mock.patch.object(tv.AdbTV, "_adb", side_effect=lambda *x: calls.append(x) or mock.Mock(returncode=0)):
            self.assertEqual(a.send("volume_down"), "adb: volume_down")
        self.assertIn(("-s", "1.2.3.4:5555", "shell", "input", "keyevent", "25"), calls)

    def test_every_action_is_mapped_by_every_keyed_driver(self):
        for d in (tv.RokuTV, tv.AdbTV):
            self.assertEqual(set(d.KEYS), set(tv.ACTIONS), d.__name__)

    def test_unknown_action_and_type(self):
        with self.assertRaises(ValueError):
            tv.DryRunTV().send("explode")
        with self.assertRaises(ValueError):
            tv.make_tv({"type": "samsung"})


if __name__ == "__main__":
    unittest.main()
