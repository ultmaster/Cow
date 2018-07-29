#!/usr/local/bin/python3

import argparse
import os
import random
import re

import subprocess

import itertools

import time
import traceback

import datetime
from colorama import Fore
from colorama import Style

CONFIG = {
    "cpp": ("{name}.cpp", "g++-7 -std=c++17 -o {name} -O2 -Dzerol -Dultmaster -fmax-errors=3 {name}.cpp", "./{name}", "{name}"),
    "py": ("{name}.py", "", "python3 {name}.py", ""),
}


def modification_date(filename):
    t = os.path.getmtime(filename)
    return datetime.datetime.fromtimestamp(t)


def parse_samples(file):
    samples = []
    with open(file) as sample_file_handler:
        lst = re.split(r"%{2,}\n", sample_file_handler.read())
    for i in range(0, len(lst), 2):
        try:
            samples.append((lst[i].strip(), lst[i + 1].strip()))
        except: pass
    return samples


def check(command, test_input, test_output, time_limit, output_limit, ignore_runtime_error=False):
    in_file = "/tmp/std_input"
    stderr_file = "/tmp/std_err"
    try:
        with open(in_file, "w") as inf:
            inf.write(test_input)
        with open(in_file) as inf, open(stderr_file, "w") as err:
            current_time = time.time()
            output = subprocess.check_output(command, stdin=inf, stderr=err, shell=True, timeout=time_limit)
            time_elapsed = time.time() - current_time
            if len(output) / 1024 > output_limit:
                raise RuntimeError("Output limit exceeded")
            output = output.decode().strip()
            if output == test_output:
                print("OK, time = %.3fs" % time_elapsed)
                return True
            print("Unexpected Output")
            print(Fore.YELLOW + "Input:\n" + test_input)
            print(Fore.GREEN + "Expected:\n" + test_output)
            print(Fore.RED + "Found:\n" + output)
            print(Style.RESET_ALL, end='')
            return False
    except subprocess.CalledProcessError:
        if ignore_runtime_error:
            with open(stderr_file, encoding='ascii') as f:
                print("Error info:")
                print(f.read().strip() + Style.RESET_ALL)
            return False
        raise
    except Exception as e:
        print("Exception found:", repr(e))
        traceback.print_exc()
        with open(stderr_file) as f:
            print(Fore.RED + "Stderr info:")
            print(f.read(4096).strip() + "\n========" + Style.RESET_ALL)
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Tester invented by cows.')

    parser.add_argument('name', metavar='Name', type=str, nargs='?', default='a',
                        help='Project name, source file should be named as <name>.cpp, sample file should be <name>.txt')
    parser.add_argument('--time', '-t', dest='time_limit', type=float, default=2,
                        help='Set the time limit (by seconds)')
    parser.add_argument('--output', dest='output_limit', type=int, default=65536,
                        help='Set the output limit (by kilobytes)')
    parser.add_argument('--sample-combine', dest="sample_combine", type=str, default='none',
                        help='Sample combination policy. Available choices are: shuffle, ordered, none')
    parser.add_argument('--check', dest='online_judge', default=False, const=True, action='store_const',
                        help='Enable online judge mode')

    args = parser.parse_args()

    print("Current working directory:", os.getcwd())
    filename, compiler, executer, dest = "", "", "", ""

    for f, c, e, d in CONFIG.values():
        if os.path.exists(f.format(name=args.name)):
            filename = f.format(name=args.name)
            compiler = c.format(name=args.name)
            executer = e.format(name=args.name)
            dest = d.format(name=args.name)

    if args.online_judge:
        compiler = compiler.replace('-Dzerol -Dultmaster', '-DONLINE_JUDGE')

    if not filename:
        raise FileNotFoundError("Source file not found")

    if compiler and (not os.path.exists(dest) or modification_date(dest) < modification_date(filename)):
        print("Running:", compiler)
        subprocess.run(compiler, shell=True, check=True)
    else:
        print("Jumping over compilation phase...")

    sample_file = args.name + ".txt"

    if not os.path.exists(sample_file):
        raise FileNotFoundError("Sample file not found")

    samples = parse_samples(sample_file)
    if args.sample_combine == "shuffle":
        random.shuffle(samples)
    if args.sample_combine in ["ordered", "shuffle"]:
        sample_in, sample_out = '', ''
        for i, o in samples:
            sample_in += i + "\n"
            sample_out += o + "\n"
        sample_in = sample_in.strip()
        sample_out = sample_out.strip()
        samples = [(sample_in, sample_out)]

    correct = 0
    for idx, (sample_in, sample_out) in enumerate(samples, start=1):
        print("Test %d... " % idx, end='')
        try:
            if check(executer, sample_in, sample_out, args.time_limit, args.output_limit):
                correct += 1
        except:
            print("Fatal Error!")
            if compiler.startswith("g++"):
                compiler = "g++-7 -g {name}.cpp -o {name}".format(name=args.name)
                print(Fore.YELLOW + "Running:", compiler)
                print("Compiling with debug option")
                subprocess.run(compiler, shell=True, check=True)
                check(executer, sample_in, sample_out, args.time_limit, args.output_limit, ignore_runtime_error=True)
                break
    print("------------------------")
    print("%d out of %d tests passed." % (correct, len(samples)))
