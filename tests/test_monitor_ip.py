import pytest
from unittest.mock import Mock, patch
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
import sys
sys.path.append('/Users/jao/workspace/jmon')
import jmon
from jmon import monitor_ip

@pytest.fixture
def mock_executor():
    with patch('concurrent.futures.ThreadPoolExecutor') as mock_exec:
        yield mock_exec.return_value

@pytest.mark.asyncio
async def test_monitor_ip_reachable(mock_executor, monkeypatch):
    # Mock the asyncio.sleep and is_reachable functions
    mock_sleep = Mock()
    monkeypatch.setattr(time, 'sleep', mock_sleep)
    
    mock_is_reachable = Mock(return_value=True)
    monkeypatch.setitem(jmon, 'is_reachable', mock_is_reachable)

    status = {'192.168.1.1': {'last_up': 0, 
                              'last_down_start': None,
                              'alert_sent': False}}
    
    # Create a simple event loop and run the function
    loop = asyncio.new_event_loop()
    await loop.run_until_complete(
        monitor_ip('192.168.1.1', status, 3600)
    )
    
    # Verify the status was updated correctly
    assert status['192.168.1.1']['last_up'] > 0
    mock_sleep.assert_called_once()

@pytest.mark.asyncio
async def test_monitor_ip_unreachable(mock_executor, monkeypatch):
    mock_sleep = Mock()
    monkeypatch.setattr(time, 'sleep', mock_sleep)
    
    mock_is_reachable = Mock(return_value=False)
    monkeypatch.setitem(jmon, 'is_reachable', mock_is_reachable)

    status = {'192.168.1.1': {'last_up': 0,
                              'last_down_start': None,
                              'alert_sent': False}}
    
    loop = asyncio.new_event_loop()
    await loop.run_until_complete(
        monitor_ip('192.168.1.1', status, 3600)
    )
    
    # Verify the status was updated correctly
    assert status['192.168.1.1']['last_down_start'] > 0
    mock_sleep.assert_called_once()
