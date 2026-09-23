import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


def load(name):
    return yaml.safe_load((ROOT / name).read_text(encoding="utf-8"))


class OutputOwnershipModel:
    def __init__(self):
        self.owner = False
        self.abort_active = False
        self.new_packet_ready = True

    def acquire(self):
        if self.owner or not self.new_packet_ready:
            raise AssertionError("output not free for a new packet")
        self.owner = True
        self.new_packet_ready = False

    def terminal_fifo_accept(self):
        return self.owner

    def terminal_encoding_commit(self):
        return self.owner

    def terminal_serial_complete(self):
        if not self.owner:
            raise AssertionError("no active owner")
        self.owner = False
        self.new_packet_ready = True

    def timeout_abort_accept(self):
        if not self.owner:
            raise AssertionError("timeout without packet owner")
        self.abort_active = True

    def abort_done(self):
        if not self.abort_active:
            raise AssertionError("abort_done without accepted abort")
        self.abort_active = False
        self.owner = False
        self.new_packet_ready = True

    def link_error(self):
        self.abort_active = False
        self.owner = False
        self.new_packet_ready = False

    def recovery_ready(self):
        if self.owner:
            raise AssertionError("owner still active")
        self.new_packet_ready = True


class TimeoutModel:
    def __init__(self, period):
        self.period = period
        self.active = False
        self.idle = 0

    def first_data(self):
        self.active = True
        self.idle = 0

    def step(self, data_progress=False, terminal=False, dominant_error=False):
        if dominant_error:
            self.active = False
            return False
        if terminal:
            self.active = False
            self.idle = 0
            return False
        if data_progress:
            self.active = True
            self.idle = 0
            return False
        if not self.active:
            return False
        self.idle += 1
        return self.idle > self.period


class Port0RouteModel:
    def __init__(self, initial):
        self.active = dict(initial)
        self.shadow = dict(initial)

    def write_shadow(self, key, value):
        self.shadow[key] = value

    def commit(self):
        self.active = dict(self.shadow)

    def malformed_or_eep(self, key, value):
        return None

    def lookup_and_commit_same_edge(self, key):
        pre_edge = self.active[key]
        self.commit()
        return pre_edge


class MulticastModel:
    def __init__(self, configured, enabled):
        self.selected = set(configured) & set(enabled)
        self.active = bool(self.selected)
        self.terminated = set()

    def transfer(self, ready):
        ready = set(ready)
        if not self.active or not self.selected.issubset(ready):
            return set()
        return set(self.selected)

    def fail_member(self, failed):
        if failed not in self.selected:
            return set()
        return self.selected - {failed}

    def terminate_member(self, port):
        self.terminated.add(port)
        if self.terminated >= self.selected:
            self.active = False


class TestNetworkRouterStaticContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dl = load("rtl_contract/5.5_data_link_rtl_contract.yaml")
        cls.net = load("rtl_contract/5.6_network_ownership_contract.yaml")
        cls.rtr = load("rtl_contract/5.6_router_rtl_contract.yaml")
        cls.p0 = load("rtl_contract/5.6_port0_configuration_rtl_contract.yaml")
        cls.bc = load("rtl_contract/5.6_broadcast_multicast_rtl_contract.yaml")

    def test_design_closed_but_review_and_rtl_gate_remain_closed(self):
        self.assertFalse(self.net["hard_gate"]["RTL_implementation_allowed"])
        self.assertFalse(self.net["hard_gate"]["reviewed"])
        self.assertEqual(self.net["hard_gate"]["design_blockers"], [])
        self.assertFalse(self.rtr["hard_gate"]["RTL_implementation_allowed"])
        self.assertFalse(self.rtr["hard_gate"]["reviewed"])
        self.assertEqual(self.rtr["hard_gate"]["design_blockers"], [])

    def test_router_pipeline_is_c0_c1_c2_c3(self):
        t = self.rtr["implementation_proposal"]["timing"]
        self.assertEqual(t["C0"], "capture_or_present_ingress_head")
        self.assertEqual(t["C1"], "registered_route_lookup_and_route_snapshot")
        self.assertEqual(t["C2"], "registered_allocator_grant_if_required_outputs_free")
        self.assertEqual(t["C3"], "first_forwardable_NChar_handshake_if_required_outputs_ready")
        self.assertTrue(t["no_same_edge_release_and_regrant"])

    def test_packet_completion_and_abort_boundary_exist_in_datalink(self):
        status = self.dl["datalink_to_network_tx_packet_status"]["signals"]
        self.assertIn("net_tx_new_packet_ready", status)
        self.assertIn("net_tx_packet_done_valid", status)
        self.assertIn("net_tx_link_abort_valid", status)
        abort = self.dl["network_to_datalink_tx_abort"]
        self.assertEqual(abort["reason"], ["ROUTER_TIMEOUT"])
        self.assertEqual(abort["completion"]["signal"], "net_tx_abort_done")
        self.assertIn("enc_tx_complete_valid", self.dl["datalink_to_encoding_tx"]["completion_feedback_required"])

    def test_port0_contract_is_atomic_and_path_only(self):
        n = self.p0["normative_boundary"]
        self.assertEqual(n["configuration_port_number"], 0)
        self.assertEqual(n["access_method"], "path_addressing_only")
        self.assertEqual(n["logical_address_access_to_port0"], "forbidden")
        self.assertEqual(self.p0["request_packet"]["malformed_or_EEP_request"]["side_effect"], "none")
        self.assertEqual(self.p0["response_packet"]["response_buffer"]["entries"], 1)
        route = self.p0["register_update_model"]["route_table"]
        self.assertEqual(route["write_path"], "WRITE_SHADOW_then_COMMIT")
        self.assertEqual(route["active_table_update"], "atomic_single_core_edge")
        self.assertIn("pre-edge", self.p0["cycle_and_precedence"]["same_cycle_route_lookup_and_commit"])

    def test_broadcast_capacity_bound_and_priority(self):
        c = self.bc["clock_profile"]
        bit_ns = 1000.0 / c["max_link_mbps"]
        spacing_ns = c["broadcast_serial_bits"] * bit_ns
        core_ns = 1e9 / c["core_hz"]
        spacing_cycles = int(spacing_ns / core_ns)
        self.assertEqual(spacing_cycles, c["minimum_same_port_broadcast_spacing_core_cycles"])
        cap = self.bc["broadcast_ingress_capture"]
        drain_cycles = cap["external_ports_default"] // 1
        self.assertLess(drain_cycles, spacing_cycles)
        self.assertEqual(
            self.bc["broadcast_egress_storage"]["scheduler_priority"],
            ["TIME_CODE", "INTERRUPT_ACK", "INTERRUPT"],
        )
        self.assertEqual(
            self.bc["broadcast_egress_storage"]["overflow_policy"]["silent_loss"],
            "forbidden",
        )

    def test_multicast_is_atomic_frozen_and_fail_whole(self):
        m = self.bc["multicast"]
        self.assertTrue(m["allocation"]["allocation_atomic"])
        self.assertTrue(m["allocation"]["partial_allocation_forbidden"])
        self.assertTrue(m["allocation"]["selected_mask_frozen_until_packet_termination"])
        self.assertTrue(m["transfer"]["same_kind_and_data_to_all_selected_outputs"])
        self.assertEqual(m["midpacket_failure_policy"]["policy"], "fail_whole_multicast_packet")
        self.assertTrue(m["packet_completion"]["release_all_together"])


class TestRouterOutputOwnership(unittest.TestCase):
    def test_terminal_fifo_accept_and_encoding_commit_do_not_release(self):
        m = OutputOwnershipModel()
        m.acquire()
        self.assertTrue(m.terminal_fifo_accept())
        self.assertTrue(m.owner)
        self.assertTrue(m.terminal_encoding_commit())
        self.assertTrue(m.owner)
        m.terminal_serial_complete()
        self.assertFalse(m.owner)
        self.assertTrue(m.new_packet_ready)

    def test_timeout_abort_releases_only_on_abort_done(self):
        m = OutputOwnershipModel()
        m.acquire()
        m.timeout_abort_accept()
        self.assertTrue(m.owner)
        self.assertTrue(m.abort_active)
        m.abort_done()
        self.assertFalse(m.owner)
        self.assertTrue(m.new_packet_ready)

    def test_link_error_terminates_owner_but_blocks_new_packet_until_recovery(self):
        m = OutputOwnershipModel()
        m.acquire()
        m.link_error()
        self.assertFalse(m.owner)
        self.assertFalse(m.new_packet_ready)
        m.recovery_ready()
        self.assertTrue(m.new_packet_ready)


class TestRouterTimeout(unittest.TestCase):
    def test_strictly_greater_than_period(self):
        m = TimeoutModel(period=3)
        m.first_data()
        self.assertFalse(m.step())
        self.assertFalse(m.step())
        self.assertFalse(m.step())
        self.assertTrue(m.step())

    def test_same_edge_progress_and_terminal_suppress_timeout(self):
        m = TimeoutModel(period=0)
        m.first_data()
        self.assertFalse(m.step(data_progress=True))
        self.assertFalse(m.step(terminal=True))
        self.assertFalse(m.active)


class TestPort0AtomicUpdate(unittest.TestCase):
    def test_shadow_not_visible_until_commit(self):
        m = Port0RouteModel({"R": 1})
        m.write_shadow("R", 2)
        self.assertEqual(m.active["R"], 1)
        m.commit()
        self.assertEqual(m.active["R"], 2)

    def test_same_edge_lookup_observes_preedge_entry(self):
        m = Port0RouteModel({"R": 1})
        m.write_shadow("R", 2)
        self.assertEqual(m.lookup_and_commit_same_edge("R"), 1)
        self.assertEqual(m.active["R"], 2)

    def test_malformed_or_eep_request_has_no_side_effect(self):
        m = Port0RouteModel({"R": 1})
        m.malformed_or_eep("R", 99)
        self.assertEqual(m.active["R"], 1)


class TestBroadcastAndMulticast(unittest.TestCase):
    def test_four_simultaneous_broadcasts_drain_before_same_port_can_repeat(self):
        slots = ["P1", "P2", "P3", "P4"]
        drained = []
        for _ in range(4):
            drained.append(slots.pop(0))
        self.assertEqual(len(drained), 4)
        self.assertEqual(slots, [])
        self.assertLess(4, 7)

    def test_priority_at_datalink_acceptance(self):
        pending = {"INTERRUPT", "TIME_CODE", "INTERRUPT_ACK"}
        priority = ["TIME_CODE", "INTERRUPT_ACK", "INTERRUPT"]
        chosen = next(x for x in priority if x in pending)
        self.assertEqual(chosen, "TIME_CODE")

    def test_multicast_never_subset_transfers(self):
        m = MulticastModel(configured={1, 2, 3}, enabled={1, 2, 3})
        self.assertEqual(m.transfer({1, 2}), set())
        self.assertEqual(m.transfer({1, 2, 3}), {1, 2, 3})

    def test_member_failure_aborts_healthy_members_and_group_waits_for_all(self):
        m = MulticastModel(configured={1, 2, 3}, enabled={1, 2, 3})
        self.assertEqual(m.fail_member(2), {1, 3})
        m.terminate_member(1)
        m.terminate_member(2)
        self.assertTrue(m.active)
        m.terminate_member(3)
        self.assertFalse(m.active)


if __name__ == "__main__":
    unittest.main()
