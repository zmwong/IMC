# IMC Python Wrapper with Logging Support
# Wraps over runIMC.py to provide logging functionality and test validation

import os
import sys
import datetime
import argparse
import re
import shutil
import subprocess
import time
try:
    import svtools.logging.toolbox as slt
except ImportError:
    # Fallback to standard logging if svtools is not available
    import logging
    slt = None

# Input Arguments
ap = argparse.ArgumentParser(description='IMC Test Wrapper with Logging')

# IMC specific arguments (commonly used)
group = ap.add_argument_group('IMC Test Arguments')
group.add_argument('xml_file', nargs='?', default='FV\MemTest.xml',
                   help='XML test file (default: FV\MemTest.xml)')
group.add_argument('-m', '--memory', dest='memory', type=int, default=100,
                   help='Memory parameter (default: 100)')
group.add_argument('--stop-on-error', action='store_true', default=True,
                   help='Stop execution on first error (default: True)')
group.add_argument('--no-stop-on-error', dest='stop_on_error', action='store_false',
                   help='Continue execution on errors (overrides --stop-on-error)')
group.add_argument('--time_to_execute', dest='time_to_execute', type=int, default=10800,
                   help='Time to execute in seconds (default: 10800 = 3 hours)')

# Wrapper specific arguments
wrapper_group = ap.add_argument_group('Wrapper Options')
wrapper_group.add_argument('-s', '--script', dest='script_args', nargs='*', 
                          help='Additional arguments to pass to runIMC.py script')
 # Removed timeout argument
wrapper_group.add_argument('-l', '--logdir', dest='log_dir', 
                          help='Custom log directory path (optional)')

args = ap.parse_args()

# Script & file path
scriptpath = os.path.abspath(__file__)
path = os.path.dirname(scriptpath)

def find_runimc_script():
    """Find runIMC.py in the current directory or parent directories"""
    
    current_dir = path
    max_levels = 5  # Limit search to 5 levels up to avoid infinite search
    
    for level in range(max_levels):
        # Check current directory
        runimc_candidate = os.path.join(current_dir, "runIMC.py")
        if os.path.exists(runimc_candidate):
            return runimc_candidate, current_dir
        
        # Move up one directory level
        parent_dir = os.path.dirname(current_dir)
        
        # If we've reached the root or can't go higher, stop
        if parent_dir == current_dir:
            break
            
        current_dir = parent_dir
    
    # If not found in parent directories, check common subdirectories
    # Start from the original script directory and check subdirectories
    search_base = path
    for root, dirs, files in os.walk(search_base):
        if "runIMC.py" in files:
            runimc_candidate = os.path.join(root, "runIMC.py")
            return runimc_candidate, root
        
        # Also check parent directories from current search root
        check_dir = os.path.dirname(search_base)
        for level in range(3):  # Check up to 3 levels up
            if check_dir != search_base:
                for sub_root, sub_dirs, sub_files in os.walk(check_dir):
                    if "runIMC.py" in sub_files:
                        runimc_candidate = os.path.join(sub_root, "runIMC.py")
                        return runimc_candidate, sub_root
                check_dir = os.path.dirname(check_dir)
                if os.path.dirname(check_dir) == check_dir:  # Reached root
                    break
    
    return None, None

# Find runIMC.py script
runimc_script, runimc_dir = find_runimc_script()

# Verify runIMC.py exists
if runimc_script is None or not os.path.exists(runimc_script):
    print("ERROR: runIMC.py not found in current directory or parent directories")
    print(f"Searched from: {path}")
    print("Please ensure runIMC.py is in the same directory tree")
    sys.exit(1)

print(f"Found runIMC.py at: {runimc_script}")
print(f"runIMC.py directory: {runimc_dir}")

# Log Path Setup (logs will be in the same directory as this script)
if args.log_dir:
    log_path = args.log_dir
else:
    log_path = os.path.join(path, 'Log', 'IMC')

if not os.path.exists(log_path):
    os.makedirs(log_path)

cleanup_path = os.path.join(log_path, 'History')
pylog_path = os.path.join(log_path, 'runIMC_wrapper.log')


# Logging Setup
def setup_logging():
    global _log
    if slt:
        # Use svtools logging if available
        _log = slt.getLogger('runIMC_wrapper', autosplit=True)
        _log.setFile(pylog_path, overwrite=True)
        _log.colorLevels = True
        _log.setConsoleFormat = 'simple'
        _log.setFileFormat = 'time'
        _log.setConsoleLevel('INFO')
        _log.setFileLevel('DEBUGALL')
    else:
        # Fallback to standard logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(pylog_path, mode='w'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        _log = logging.getLogger('runIMC_wrapper')

# Test validation patterns (modified based on IMC tool's output)
test_patterns = {
    'complete_msg': r"Post-processing completed successfully",
    'pass_msg': r"COMPLETED SUCCESSFULLY",
    'fail_msg': r"COMPLETED WITH ERRORS"
}

def log_info(message):
    if slt:
        _log.info(message)
    else:
        _log.info(message)

def log_error(message):
    if slt:
        _log.error(message)
    else:
        _log.error(message)

def log_success(message):
    if slt:
        _log.success(message)
    else:
        _log.info(f"SUCCESS: {message}")

def build_imc_command():
    """Build the command for runIMC.py with parsed arguments"""
    
    cmd = [sys.executable, runimc_script]
    
    # Add XML file
    cmd.append(args.xml_file)
    
    # Add memory parameter
    cmd.extend(['-m', str(args.memory)])
    
    # Add stop-on-error if specified
    if args.stop_on_error:
        cmd.append('--stop-on-error')
    
    # Add time_to_execute if specified
    if args.time_to_execute:
        cmd.extend(['--time_to_execute', str(args.time_to_execute)])
    
    # Add any additional script arguments
    if args.script_args:
        cmd.extend(args.script_args)
    
    return cmd

def run_imc_with_logging():
    """Execute runIMC.py and capture all output for logging"""
    
    # Build command using parsed arguments
    cmd = build_imc_command()
    
    log_info('Starting runIMC.py execution')
    log_info(f'Command: {" ".join(cmd)}')
    log_info(f'Working directory: {runimc_dir}')
    log_info(f'XML File: {args.xml_file}')
    log_info(f'Memory Parameter: {args.memory}')
    log_info(f'Stop on Error: {args.stop_on_error}')
    if args.time_to_execute:
        log_info(f'Time to Execute: {args.time_to_execute} seconds')
    
    # Only write to latest_results.log in main log dir
    latest_log_path = os.path.join(log_path, 'latest_results.log')
    if not os.path.exists(cleanup_path):
        os.makedirs(cleanup_path)
    try:
        start_time = time.time()
        with open(latest_log_path, 'w') as latest_log:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                cwd=runimc_dir,
                bufsize=1
            )
            log_info(f'Process started with PID: {process.pid}')
            log_info(f'Latest log: {latest_log_path}')
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    latest_log.write(output)
                    latest_log.flush()
                    print(output.strip())
            return_code = process.poll()
            execution_time = time.time() - start_time
            log_info(f'Process completed with return code: {return_code}')
            log_info(f'Execution time: {execution_time:.2f} seconds')
            return return_code == 0, latest_log_path, 'COMPLETED'
    except Exception as e:
        log_error(f'Error executing runIMC.py: {str(e)}')
        return False, latest_log_path, 'ERROR'

def analyze_test_results(output_log_path):
    """Analyze the captured output for test results"""
    
    if not os.path.exists(output_log_path):
        log_error(f'Output log file not found: {output_log_path}')
        return False
    
    log_info('Analyzing test results...')
    
    complete_check = False
    pass_found = False
    fail_found = False
    error_lines = []
    try:
        with open(output_log_path, 'r') as log_file:
            content = log_file.read()
            lines = content.split('\n')
            for line in lines:
                # Check for completion
                if re.search(test_patterns['complete_msg'], line, re.IGNORECASE):
                    complete_check = True
                    log_info(f'Found completion indicator: {line.strip()}')
                # Check for pass
                if re.search(test_patterns['pass_msg'], line, re.IGNORECASE):
                    pass_found = True
                    log_info(f'Found PASS: {line.strip()}')
                # Check for fail
                if re.search(test_patterns['fail_msg'], line, re.IGNORECASE):
                    fail_found = True
                    log_error(f'Found FAIL: {line.strip()}')
                # Collect error lines
                if '[error]' in line.lower():
                    error_lines.append(line)
    except Exception as e:
        log_error(f'Error analyzing results: {str(e)}')
        return False, None
    # Result summary
    log_info(f'Analysis Results:')
    log_info(f'  - Test Completed: {complete_check}')
    log_info(f'  - Pass Found: {pass_found}')
    log_info(f'  - Fail Found: {fail_found}')
    # Determine overall result
    if not complete_check:
        log_error('Test did not complete successfully - possible user interruption or tool error')
        return False, error_lines
    if fail_found:
        log_error('Test FAILED - Tool completed with errors')
        return False, error_lines
    if pass_found:
        log_success('Test PASSED - Tool completed successfully')
        return True, error_lines
    # If completion found but no explicit pass/fail found
    log_info('Test completed but no explicit pass/fail indicators found')
    return True, error_lines

def cleanup_old_logs():
    """Clean up old latest_results.log files by moving them to history"""
    
    # Ensure history directory exists
    if not os.path.exists(cleanup_path):
        os.makedirs(cleanup_path)
    
    latest_log_path = os.path.join(log_path, 'latest_results.log')
    
    try:
        # If latest_results.log exists, move it to history with timestamp
        if os.path.exists(latest_log_path):
            # Get file modification time
            file_time = datetime.datetime.fromtimestamp(os.path.getmtime(latest_log_path))
            timestamp = file_time.strftime("%Y-%m-%d_%H-%M-%S")
            
            # Create new filename with timestamp
            archived_name = f'latest_results_{timestamp}.log'
            archived_path = os.path.join(cleanup_path, archived_name)
            
            # Move to history
            shutil.move(latest_log_path, archived_path)
            log_info(f'Moved previous latest_results.log to history: {archived_name}')
        
        # Optional: Clean up very old files in history (older than 30 days)
        current_time = datetime.datetime.now()
        for file in os.listdir(cleanup_path):
            if file.endswith('.log'):
                file_path = os.path.join(cleanup_path, file)
                if os.path.isfile(file_path):
                    file_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                    # Remove files older than 30 days
                    if (current_time - file_time).total_seconds() > (30 * 24 * 3600):
                        os.remove(file_path)
                        log_info(f'Removed old log file: {file}')
                
    except Exception as e:
        log_error(f'Error during log cleanup: {str(e)}')

def main():
    """Main execution function"""
    
    # Setup logging
    setup_logging()
    
    log_info('=' * 60)
    log_info('IMC Test Wrapper Started')
    log_info(f'Timestamp: {datetime.datetime.now()}')
    log_info('=' * 60)
    
    try:
        # Cleanup old logs first (move existing latest_results.log to history)
        cleanup_old_logs()
        
        # Execute runIMC.py with logging
        success, output_log_path, status = run_imc_with_logging()
        if status == 'ERROR':
            log_error('Error occurred during test execution')
            sys.exit(505)
        # Analyze results (now using latest_results.log)
        test_passed, error_lines = analyze_test_results(output_log_path)
        # Move and rename the latest_results log to History with PASS_/FAIL_ prefix
        latest_log_path = output_log_path
        # Get file modification time for timestamp
        if os.path.exists(latest_log_path):
            file_time = datetime.datetime.fromtimestamp(os.path.getmtime(latest_log_path))
            timestamp = file_time.strftime("%Y-%m-%d_%H-%M-%S")
            if test_passed:
                new_log_name = f'PASS_latest_results_{timestamp}.log'
            else:
                new_log_name = f'FAIL_latest_results_{timestamp}.log'
            new_log_path = os.path.join(cleanup_path, new_log_name)
            shutil.copy2(latest_log_path, new_log_path)
            log_info(f'Copied and renamed log file to: {new_log_name}')
        # If fail, append error summary to runIMC_wrapper.log
        if not test_passed and error_lines:
            try:
                with open(pylog_path, 'a') as pylog:
                    pylog.write('\n===== ERROR SUMMARY FROM TEST LOG =====\n')
                    for err in error_lines:
                        pylog.write(err + '\n')
                    pylog.write('===== END ERROR SUMMARY =====\n')
                log_info('Error summary appended to runIMC_wrapper.log')
            except Exception as e:
                log_error(f'Failed to append error summary: {str(e)}')
        # Exit codes and messages
        if test_passed:
            log_success('IMC Test completed successfully')
            log_info(f'Latest results available at: {output_log_path}')
            sys.exit(0)
        else:
            log_error('IMC Test failed based on output analysis')
            sys.exit(500)
            
    except KeyboardInterrupt:
        log_error('Test execution interrupted by user')
        sys.exit(502)
    except Exception as e:
        log_error(f'Unexpected error: {str(e)}')
        sys.exit(503)
    finally:
        log_info('IMC Test Wrapper finished')
        log_info('=' * 60)

if __name__ == '__main__':
    main()