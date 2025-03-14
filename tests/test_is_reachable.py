import pytest
from unittest.mock import patch, Mock, MagicMock
import subprocess
import time
import sys
sys.path.append('/Users/jao/workspace/jmon')
from jmon import is_reachable

@pytest.fixture
def mock_subprocess():
    with patch('subprocess.run') as mock_run:
        yield mock_run

@pytest.fixture
def mock_subprocess():
    with patch('subprocess.run') as mock_run:
        yield mock_run

def test_is_reachable_success(mock_subprocess, monkeypatch):
    # Setup mock to return success (returncode 0)
    mock_subprocess.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout='1 packets transmitted, 1 received, 0% packet loss',
        stderr=''
    )
    
    result = is_reachable('192.168.1.1')
    assert result is True

def test_is_reachable_failure(mock_subprocess, monkeypatch):
    # Setup mock to return failure (returncode !=0)
    mock_subprocess.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=1,
        stdout='',
        stderr='ping failed'
    )
    
    result = is_reachable('192.168.1.1')
    assert result is False

def test_is_reachable_timeout(mock_subprocess, monkeypatch):
    with patch('subprocess.run') as mock_run:
        # Setup mock to timeout
        mock_run.side_effect = subprocess.TimeoutError()
        
        result = is_reachable('192.168.1.1')
        assert result is False
