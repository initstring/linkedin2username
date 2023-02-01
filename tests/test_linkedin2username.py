import linkedin2username
from linkedin2username import NameMutator

# Test name mutations

TEST_NAMES = {
    1: "John Smith",
    2: "John Davidson-Smith",
    3: "John-Paul Smith-Robinson",
    4: "José Gonzáles",
}


def test_f_last():
    name = TEST_NAMES[1]
    mutator = NameMutator(name)
    assert mutator.f_last() == set(["jsmith", ])

    name = TEST_NAMES[2]
    mutator = NameMutator(name)
    assert mutator.f_last() == set(["jsmith", "jdavidson"])

    name = TEST_NAMES[3]
    mutator = NameMutator(name)
    assert mutator.f_last() == set(["jsmith", "jrobinson"])

    name = TEST_NAMES[4]
    mutator = NameMutator(name)
    assert mutator.f_last() == set(["jgonzales", ])


def test_f_dot_last():
    name = TEST_NAMES[1]
    mutator = NameMutator(name)
    assert mutator.f_dot_last() == set(["j.smith", ])

    name = TEST_NAMES[2]
    mutator = NameMutator(name)
    assert mutator.f_dot_last() == set(["j.smith", "j.davidson"])

    name = TEST_NAMES[3]
    mutator = NameMutator(name)
    assert mutator.f_dot_last() == set(["j.smith", "j.robinson"])

    name = TEST_NAMES[4]
    mutator = NameMutator(name)
    assert mutator.f_dot_last() == set(["j.gonzales", ])


def test_last_f():
    name = TEST_NAMES[1]
    mutator = NameMutator(name)
    assert mutator.last_f() == set(["smithj", ])

    name = TEST_NAMES[2]
    mutator = NameMutator(name)
    assert mutator.last_f() == set(["smithj", "davidsonj"])

    name = TEST_NAMES[3]
    mutator = NameMutator(name)
    assert mutator.last_f() == set(["smithj", "robinsonj"])

    name = TEST_NAMES[4]
    mutator = NameMutator(name)
    assert mutator.last_f() == set(["gonzalesj", ])


def test_first_dot_last():
    name = TEST_NAMES[1]
    mutator = NameMutator(name)
    assert mutator.first_dot_last() == set(["john.smith", ])

    name = TEST_NAMES[2]
    mutator = NameMutator(name)
    assert mutator.first_dot_last() == set(["john.smith", "john.davidson"])

    name = TEST_NAMES[3]
    mutator = NameMutator(name)
    assert mutator.first_dot_last() == set(["john.smith", "john.robinson"])

    name = TEST_NAMES[4]
    mutator = NameMutator(name)
    assert mutator.first_dot_last() == set(["jose.gonzales", ])


def test_first_l():
    name = TEST_NAMES[1]
    mutator = NameMutator(name)
    assert mutator.first_l() == set(["johns", ])

    name = TEST_NAMES[2]
    mutator = NameMutator(name)
    assert mutator.first_l() == set(["johns", "johnd"])

    name = TEST_NAMES[3]
    mutator = NameMutator(name)
    assert mutator.first_l() == set(["johns", "johnr"])

    name = TEST_NAMES[4]
    mutator = NameMutator(name)
    assert mutator.first_l() == set(["joseg", ])


def test_first():
    name = TEST_NAMES[1]
    mutator = NameMutator(name)
    assert mutator.first() == set(["john", ])

    name = TEST_NAMES[2]
    mutator = NameMutator(name)
    assert mutator.first() == set(["john", ])

    name = TEST_NAMES[3]
    mutator = NameMutator(name)
    assert mutator.first() == set(["john", ])

    name = TEST_NAMES[4]
    mutator = NameMutator(name)
    assert mutator.first() == set(["jose", ])


def test_clean_name():
    mutator = NameMutator("xxx")
    assert mutator.clean_name("  🙂Ànèôõö    ßï🙂  ") == "aneooo ssi"

    name = "Dr. Hannibal Lecter, PhD."
    assert mutator.clean_name(name) == "hannibal lecter"

    name = "Mr. Fancy Pants MD, PhD, MBA"
    assert mutator.clean_name(name) == "fancy pants"

    name = "Mr. Cert Dude (OSCP, OSCE)"
    assert mutator.clean_name(name) == "cert dude"


def test_split_name():
    mutator = NameMutator("xxx")

    name = "madonna wayne gacey"
    assert mutator.split_name(name) == {"first": "madonna", "second": "wayne", "last": "gacey"}

    name = "twiggy ramirez"
    assert mutator.split_name(name) == {"first": "twiggy", "second": "", "last": "ramirez"}

    name = "brian warner is marilyn manson"
    assert mutator.split_name(name) == {"first": "brian", "second": "marilyn", "last": "manson"}


def test_find_employees():
    with open("tests/mock-employee-response", "r") as infile:
        result = infile.read()
    employees = linkedin2username.find_employees(result)

    assert len(employees) == 2
    assert employees[0] == {'full_name': 'Michael Myers', 'occupation': 'Camp Counsellor'}
    assert employees[1] == {'full_name': 'Freddy Krueger', 'occupation': 'Babysitter'}

    result = '{"elements": []}'
    assert not linkedin2username.find_employees(result)

