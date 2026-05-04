"""Unit tests for tsdp.decision_function."""
import numpy as np
import pytest

from tsdp.config import TSDPConfig, PAPER_DEFAULT
from tsdp.decision_function import phi, phi_batch


class TestPhi:
    def test_zero_inputs_give_only_depth_term(self):
        config = PAPER_DEFAULT
        # At level 0 with R = S = 0, phi = gamma * 1 = 0.1
        result = phi(R=0.0, S=0.0, level=0,
                     R_max=1.0, S_max=1.0, config=config)
        assert result == pytest.approx(config.gamma)

    def test_at_max_level_depth_term_zero(self):
        config = PAPER_DEFAULT
        result = phi(R=0.0, S=0.0, level=config.L_max,
                     R_max=1.0, S_max=1.0, config=config)
        assert result == pytest.approx(0.0)

    def test_handles_zero_R_max(self):
        # Should not divide by zero; returns 0 contribution from R term
        config = PAPER_DEFAULT
        result = phi(R=0.0, S=0.0, level=0,
                     R_max=0.0, S_max=1.0, config=config)
        # Only depth term remains: gamma * 1 = 0.1
        assert result == pytest.approx(config.gamma)

    def test_weighting_correct(self):
        config = TSDPConfig(alpha=0.6, beta=0.3, gamma=0.1,
                            L0=0, L_max=10)
        # R/R_max = 1, S/S_max = 1, depth = 1
        # phi = 0.6 + 0.3 + 0.1 = 1.0
        result = phi(R=1.0, S=1.0, level=0,
                     R_max=1.0, S_max=1.0, config=config)
        assert result == pytest.approx(1.0)


class TestPhiBatch:
    def test_matches_scalar_version(self):
        config = PAPER_DEFAULT
        rng = np.random.default_rng(0)
        R = rng.uniform(0, 1, size=20)
        S = rng.uniform(0, 1, size=20)
        levels = rng.integers(config.L0, config.L_max + 1, size=20)

        batch = phi_batch(R, S, levels.astype(float),
                          R_max=1.0, S_max=1.0, config=config)
        scalar = np.array([
            phi(R[i], S[i], int(levels[i]), 1.0, 1.0, config)
            for i in range(20)
        ])
        np.testing.assert_allclose(batch, scalar, rtol=1e-12)
