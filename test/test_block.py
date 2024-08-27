from pathlib import Path

import numpy as np
import pytest

from flopy4.array import MFArray
from flopy4.block import MFBlock
from flopy4.compound import MFKeystring, MFRecord
from flopy4.scalar import MFDouble, MFFilename, MFInteger, MFKeyword, MFString


class TestBlock(MFBlock):
    __test__ = False  # tell pytest not to collect

    k = MFKeyword(description="keyword", type="keyword")
    i = MFInteger(description="int", type="integer")
    d = MFDouble(description="double", type="double")
    s = MFString(description="string", optional=False, type="string")
    f = MFFilename(description="filename", optional=False, type="filename")
    a = MFArray(description="array", shape=(3,), type="array")
    r = MFRecord(
        params={
            "rk": MFKeyword(),
            "ri": MFInteger(),
            "rd": MFDouble(),
        },
        description="record",
        optional=False,
        type="record",
    )


def test_members():
    params = TestBlock.params
    assert len(params) == 7

    k = params.k
    assert isinstance(k, MFKeyword)
    assert k.description == "keyword"
    assert k.optional

    i = params.i
    assert isinstance(i, MFInteger)
    assert i.description == "int"
    assert i.optional

    d = params.d
    assert isinstance(d, MFDouble)
    assert d.description == "double"
    assert d.optional

    s = params.s
    assert isinstance(s, MFString)
    assert s.description == "string"
    assert not s.optional

    f = params.f
    assert isinstance(f, MFFilename)
    assert f.description == "filename"
    assert not f.optional

    a = params.a
    assert isinstance(a, MFArray)
    assert a.description == "array"
    assert a.optional

    r = params.r
    assert isinstance(r, MFRecord)
    assert r.description == "record"
    assert not r.optional


def test_load_write(tmp_path):
    name = "options"
    fpth = tmp_path / f"{name}.txt"
    with open(fpth, "w") as f:
        f.write(f"BEGIN {name.upper()}\n")
        f.write("  K\n")
        f.write("  I 1\n")
        f.write("  D 1.0\n")
        f.write("  S value\n")
        f.write(f"  F FILEIN {fpth}\n")
        f.write("  R RK RI 2 RD 2.0\n")
        # f.write("  RK RI 2 RD 2.0\n")
        # f.write("  RK 2 2.0\n")
        f.write("  A\n    INTERNAL\n      1.0 2.0 3.0\n")
        f.write(f"END {name.upper()}\n")

    # test block load
    with open(fpth, "r") as f:
        block = TestBlock.load(f)

        # check parameter specification
        assert isinstance(TestBlock.k, MFKeyword)
        assert TestBlock.k.name == "k"
        assert TestBlock.k.block == "options"
        assert TestBlock.k.description == "keyword"

        assert isinstance(TestBlock.r, MFRecord)
        assert TestBlock.r.name == "r"
        assert len(TestBlock.r.params) == 3
        assert isinstance(TestBlock.r.params["rk"], MFKeyword)
        assert isinstance(TestBlock.r.params["ri"], MFInteger)
        assert isinstance(TestBlock.r.params["rd"], MFDouble)

        # check parameter values
        assert block.k and block.value["k"]
        assert block.i == block.value["i"] == 1
        assert block.d == block.value["d"] == 1.0
        assert block.s == block.value["s"] == "value"
        assert block.f == block.value["f"] == fpth
        assert np.allclose(block.a, np.array([1.0, 2.0, 3.0]))
        assert np.allclose(block.value["a"], np.array([1.0, 2.0, 3.0]))
        assert block.r == block.value["r"] == {"rd": 2.0, "ri": 2, "rk": True}

    # test block write
    fpth2 = tmp_path / f"{name}2.txt"
    with open(fpth2, "w") as f:
        block.write(f)
    with open(fpth2, "r") as f:
        lines = f.readlines()
        assert "BEGIN OPTIONS \n" in lines
        assert "  K\n" in lines
        assert "  I 1\n" in lines
        assert "  D 1.0\n" in lines
        assert "  S value\n" in lines
        assert f"  F FILEIN {fpth}\n" in lines
        assert "  A\n" in lines
        assert "    INTERNAL\n" in lines
        assert "      1.0 2.0 3.0\n" in lines
        assert "  R  RK  RI 2  RD 2.0\n" in lines
        assert "END OPTIONS\n" in lines


class IndexedBlock(MFBlock):
    ks = MFKeystring(
        params={
            "first": MFKeyword(),
            "frequency": MFInteger(),
        },
        description="keystring",
        optional=False,
    )


def test_load_write_indexed(tmp_path):
    block_name = "indexed"
    fpth = tmp_path / f"{block_name}.txt"
    with open(fpth, "w") as f:
        f.write(f"BEGIN {block_name.upper()} 1\n")
        f.write("  FIRST\n")
        f.write(f"END {block_name.upper()}\n")
        f.write("\n")
        f.write(f"BEGIN {block_name.upper()} 2\n")
        f.write("  FIRST\n")
        f.write("  FREQUENCY 2\n")
        f.write(f"END {block_name.upper()}\n")

    with open(fpth, "r") as f:
        period1 = IndexedBlock.load(f)
        period2 = IndexedBlock.load(f)

        # todo: go to 0-based indexing
        assert period1.index == 1
        assert period2.index == 2

        # class attributes as param specification
        assert isinstance(IndexedBlock.ks, MFKeystring)
        assert IndexedBlock.ks.name == "ks"
        assert IndexedBlock.ks.block == block_name

        # instance attribute as shortcut to param value
        assert period1.ks == {"first": True}
        assert period2.ks == {"first": True, "frequency": 2}


def test_set_value():
    block = TestBlock(name="test")
    block.value = {
        "k": True,
        "i": 42,
        "d": 2.0,
        "s": "hello world",
    }
    assert block.k


def test_set_value_unrecognized():
    block = TestBlock(name="test")
    with pytest.raises(ValueError):
        block.value = {"p": Path.cwd()}
