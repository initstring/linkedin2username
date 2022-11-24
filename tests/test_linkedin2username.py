from linkedin2username import NameMutator

# Test name mutations

TEST_NAMES = {
    1: "John Smith",
    2: "John Davidson-Smith",
    3: "John-Paul Smith-Robinson",
    4: "José Gonzáles"
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
