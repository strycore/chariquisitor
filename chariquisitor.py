import json
from collections import defaultdict


SEGMENTS = ['workings', 'shinies', 'controls', 'fun']
REVIEWERS = ['venn', 'jordan', 'pedro']


def iter_charis():
    with open('charis.json') as charis_file:
        charis = json.load(charis_file)

    for chari in charis:
        if set(chari['scores'].keys()) != set(SEGMENTS):
            continue
        for segment in chari['scores']:
            if set(chari['scores'][segment].keys()) != set(REVIEWERS):
                continue
        yield chari


def get_totals():

    totals = {}
    for segment in SEGMENTS:
        totals[segment] = defaultdict(int)
    for chari in iter_charis():
        for segment in SEGMENTS:
            for reviewer, score in chari['scores'][segment].items():
                totals[segment][reviewer] += score
    return totals


grand_totals = defaultdict(int)
for segment, reviews in get_totals().items():
    verdicts = {
        'workings': "%s has the best machine! %s and %s can only try to keep up!",
        'shinies': "%s appreciates the arts more than %s or %s!",
        'controls': "%s is fully in control! %s and %s are just clumsy!",
        'fun': "%s knows how to have a good time! Unlike those goths %s and %s!",
        'all': "Overall, %s likes video games more than %s or %s."
    }
    winners = tuple([
        reviewer.capitalize()
        for reviewer in reversed(
            sorted(reviews.iterkeys(), key=(lambda key: reviews[key]))
        )
    ])
    print(verdicts[segment] % winners)
    for reviewer, score in reviews.items():
        grand_totals[reviewer] += score

print(verdicts['all'] % tuple([
    reviewer.capitalize()
    for reviewer in reversed(
        sorted(grand_totals.iterkeys(), key=(lambda key: reviews[key]))
    )
]))
