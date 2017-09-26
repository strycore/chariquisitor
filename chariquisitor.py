import json
from collections import defaultdict


SEGMENTS = ['workings', 'shinies', 'controls', 'fun']
REVIEWERS = ['venn', 'jordan', 'pedro']


def iter_charis():
    with open('charis.json') as charis_file:
        charis = json.load(charis_file)

    for chari in charis:
        if not chari['name']:
            continue
        if set(chari['scores'].keys()) != set(SEGMENTS):
            continue
        reviewers_ok = True
        for segment in chari['scores']:
            if set(chari['scores'][segment].keys()) != set(REVIEWERS):
                reviewers_ok = False
                break
        if not reviewers_ok:
            continue
        yield chari


def get_totals_per_reviewer():
    totals = {}
    for segment in SEGMENTS:
        totals[segment] = defaultdict(int)
    for chari in iter_charis():
        for segment in SEGMENTS:
            for reviewer, score in chari['scores'][segment].items():
                totals[segment][reviewer] += score
    return totals


def get_totals_per_game():
    totals = {}
    for chari in iter_charis():
        name = "{} ({})".format(chari['name'], chari['episode'])
        totals[name] = defaultdict(int)
        for segment in SEGMENTS:
            for reviewer in REVIEWERS:
                reviewer_score = chari['scores'][segment][reviewer]
                totals[name][segment] += reviewer_score
                totals[name]['all'] += reviewer_score
    return totals


def get_fair_score(scores):
    return sum([scores[segment] for segment in SEGMENTS]) / 12


def get_lgc_score(scores):
    return sum([scores[segment] // 3 for segment in SEGMENTS]) // 4


def print_reviewers_stats():
    grand_totals = defaultdict(int)
    for segment, reviews in get_totals_per_reviewer().items():
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
                sorted(reviews.keys(), key=(lambda key: reviews[key]))
            )
        ])
        print(verdicts[segment] % winners)
        print(', '.join(["{}: {}".format(reviewer.capitalize(), reviews[reviewer]) for reviewer in REVIEWERS]))
        for reviewer, score in reviews.items():
            grand_totals[reviewer] += score

    print(verdicts['all'] % tuple([
        reviewer.capitalize()
        for reviewer in reversed(
            sorted(grand_totals.keys(), key=(lambda key: grand_totals[key]))
        )
    ]))
    print(', '.join(["{}: {}".format(reviewer.capitalize(), grand_totals[reviewer]) for reviewer in REVIEWERS]))


def print_top_games(games_totals, top=True, size=10):
    for segment in SEGMENTS + ['all']:
        print("\n=== %s %i GAMES IN %s SEGMENT ===" % ('TOP' if top else 'BOTTOM', size, segment.upper()))
        for name in [
            name for name in sorted(games_totals.keys(), key=(lambda key: games_totals[key][segment]), reverse=top)
        ][:10]:
            print("{}:  {}".format(name, games_totals[name][segment]))


def print_score_fairness(games_totals, fair=True, size=10):
    score_fairness = {}
    for game, scores in games_totals.items():
        fair_score = get_fair_score(scores)
        lgc_score = get_lgc_score(scores)
        score_fairness[game] = {
            'fair': fair_score,
            'lgc': lgc_score,
            'diff': fair_score - lgc_score,
            'game': game
        }

    print("\n=== %i %s FAIRLY REVIEWED GAMES ===" % (size, 'MOST' if fair else 'LEAST'))
    for game in [
        game for game in sorted(score_fairness.keys(),
                                key=(lambda game: score_fairness[game]['diff']),
                                reverse=not fair)
    ][:size]:
        print("%(game)s -- Fair score: %(fair)0.2f; LGC: %(lgc)i" % score_fairness[game])


if __name__ == '__main__':
    games_totals = get_totals_per_game()
    print("%i full reviews available" % len(games_totals))
    print_top_games(games_totals)
    print_top_games(games_totals, top=False)
    print_score_fairness(games_totals)
    print_score_fairness(games_totals, fair=False)
    print()
    print_reviewers_stats()
