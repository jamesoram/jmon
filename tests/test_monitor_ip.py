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

pytestmark = pytest.mark.asyncio

@pytestmark = pytest.mark.asyncio

@pytest.mark.asyncio
@pytest.mark.parametrize("initial_alert_sent,status_before,status_after", [
    (False, None, False),
    (True, None, True)
])
async def test_monitor_ip_behavior(mock_executor, monkeypatch, initial_alert_sent, status_before, status_after):
    # Mock the asyncio.sleep and is_reachable functions
    mock_sleep = Mock()
    monkeypatch.setattr(time, 'sleep', mock_sleep)
    
    mock_is_reachable = Mock(return_value=True)
    monkeypatch.setattr('jmon.is_reachable', mock_is_reachable)

    status = {'192.168.1.1': {'last_up': 0, 
                              'last_down_start': None,
                              'alert_sent': False}}
    
    # Create a simple event loop and run the function
async def main():
    with patch('jmon.is_reachable') as mock_is_reachable:
        if 'setup' in locals():  # This is a weird way to check for setup
            pass
                
    return await monitor_ip('192.168.1.1', status, 3600)
    
result = anyio.run(main)
    
    # Verify the status was updated correctly
    assert status['192.168.1.1']['last_up'] > 0
    mock_sleep.assert_called_once()

pytestmark = pytest.mark.asyncio

@pytest.mark.asyncio
@pytest.mark.parametrize("initial_alert_sent,status_before,status_after", [
    (False, None, False),
    (True, None, True)
])
async def test_monitor_ip_unreachable(mock_executor, monkeypatch, initial_alert_sent, status_before, status_after):
    mock_sleep = Mock()
    monkeypatch.setattr(time, 'sleep', mock_sleep)
    
    mock_is_reachable = Mock(return_value=False) 
    monkeypatch.setattr('jmon.is_reachable', mock_is_reachable)

    # Setup test data
    status = {'192.168.1.1': {
        'last_up': 0,
        'last_down_start': status_before,
        'alert_sent': initial_alert_sent
    }}
    
async def main():
    with patch('jmon.is_reachable') as mock_is_reachable:
        if 'setup' in locals():  # This is a weird way to check for setup
            pass
                
    return await monitor_ip('192.168.1.1', status, 3600)
    
result = anyio.run(main)
    
    # Verify the status was updated correctly
    new_status = status['192.168.1.1']
    assert (new_status['alert_sent'] == status_after) and \
           (new_status['last_down_start'] is not None)
