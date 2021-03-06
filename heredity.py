import csv
import itertools
import sys

PROBS = {

    # Unconditional probabilities for having gene
    "gene": {
        2: 0.01,
        1: 0.03,
        0: 0.96
    },

    "trait": {

        # Probability of trait given two copies of gene
        2: {
            True: 0.65,
            False: 0.35
        },

        # Probability of trait given one copy of gene
        1: {
            True: 0.56,
            False: 0.44
        },

        # Probability of trait given no gene
        0: {
            True: 0.01,
            False: 0.99
        }
    },

    # Mutation probability
    "mutation": 0.01
}


def main():

    # Check for proper usage
    if len(sys.argv) != 2:
        sys.exit("Usage: python heredity.py data.csv")
    people = load_data(sys.argv[1])

    # Keep track of gene and trait probabilities for each person
    probabilities = {
        person: {
            "gene": {
                2: 0,
                1: 0,
                0: 0
            },
            "trait": {
                True: 0,
                False: 0
            }
        }
        for person in people
    }

    # Loop over all sets of people who might have the trait
    names = set(people)
    for have_trait in powerset(names):

        # Check if current set of people violates known information
        fails_evidence = any(
            (people[person]["trait"] is not None and
             people[person]["trait"] != (person in have_trait))
            for person in names
        )
        if fails_evidence:
            continue

        # Loop over all sets of people who might have the gene
        for one_gene in powerset(names):
            for two_genes in powerset(names - one_gene):

                # Update probabilities with new joint probability
                p = joint_probability(people, one_gene, two_genes, have_trait)
                update(probabilities, one_gene, two_genes, have_trait, p)

    # Ensure probabilities sum to 1
    normalize(probabilities)

    # Print results
    for person in people:
        print(f"{person}:")
        for field in probabilities[person]:
            print(f"  {field.capitalize()}:")
            for value in probabilities[person][field]:
                p = probabilities[person][field][value]
                print(f"    {value}: {p:.4f}")


def load_data(filename):
    """
    Load gene and trait data from a file into a dictionary.
    File assumed to be a CSV containing fields name, mother, father, trait.
    mother, father must both be blank, or both be valid names in the CSV.
    trait should be 0 or 1 if trait is known, blank otherwise.
    """
    data = dict()
    with open(filename) as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["name"]
            data[name] = {
                "name": name,
                "mother": row["mother"] or None,
                "father": row["father"] or None,
                "trait": (True if row["trait"] == "1" else
                          False if row["trait"] == "0" else None)
            }
    return data


def powerset(s):
    """
    Return a list of all possible subsets of set s.
    """
    s = list(s)
    return [
        set(s) for s in itertools.chain.from_iterable(
            itertools.combinations(s, r) for r in range(len(s) + 1)
        )
    ]


def joint_probability(people, one_gene, two_genes, have_trait):
    """
    Compute and return a joint probability.

    The probability returned should be the probability that
        * everyone in set `one_gene` has one copy of the gene, and
        * everyone in set `two_genes` has two copies of the gene, and
        * everyone not in `one_gene` or `two_gene` does not have the gene, and
        * everyone in set `have_trait` has the trait, and
        * everyone not in set` have_trait` does not have the trait.
    """
    def haveParents(person):
        if people[person]["mother"] and people[person]["father"]:
            return True
        return False
    
    def howManyGenes(person):
        if person in one_gene:
            return 1
        if person in two_genes:
            return 2
        return 0

    def returnTrait(person, passTrait):
        '''
        Returns the probability that given person (in that case, a parent) 
        passes a trait forward.
        If the passTrait is True, the returned probability means that the person will 
        pass the gene and if it is False, means that don't
        '''
        genes = howManyGenes(person)
        ret = 0
        if passTrait:
            if genes == 0:
                # With 0 genes, the only way to pass the trait is with mutation
                ret = PROBS["mutation"]
            elif genes == 1:
                # If a parent has one copy of the gene, then the gene is passed 
                # on to the child with probability 0.5. 
                ret = 0.5 
            else: # genes == 2
                # If a parent has two copies of the gene, 
                # then they will pass the gene on to the child 
                # The only way it doesn't occurs is with the chance it mutates
                ret = 1 - PROBS["mutation"]
        else:
            if genes == 0:
                # If a parent has no copies of the gene, 
                # then they will not pass the gene on to the child
                # The only way it doesn't occurs is with the chance it mutates
                ret = 1 - PROBS["mutation"]
            elif genes == 1:
                ret = 0.5 
            else: # genes == 2
                # With 2 genes, the only way to not pass the trait is with mutation
                ret = PROBS["mutation"]
        return ret
    
    test = {person: 1 for person in people}
    for person in people:
        genes = howManyGenes(person)
        if haveParents(person):
            mother, father = people[person]["mother"], people[person]["father"]
            if genes == 0:
                # Not get from mother and father
                test[person] *= returnTrait(father, False) * returnTrait(mother, False)
            elif genes == 1:
                # Gets the gene from mother and not father
                test[person] *= returnTrait(father, False) * returnTrait(mother, True)
                # Or gets the gene from his father and not his mother
                test[person] += returnTrait(father, True) * returnTrait(mother, False)
            else: # genes == 2
                # Gets from mother and father
                test[person] *= returnTrait(father, True) * returnTrait(mother, True)
        else:
            test[person] *= PROBS["gene"][genes]
        
        test[person] *= PROBS["trait"][genes][person in have_trait]
    
    probability = 1
    for value in test.values():
        probability *= value
    return probability


def update(probabilities, one_gene, two_genes, have_trait, p):
    """
    Add to `probabilities` a new joint probability `p`.
    Each person should have their "gene" and "trait" distributions updated.
    Which value for each distribution is updated depends on whether
    the person is in `have_gene` and `have_trait`, respectively.
    """
    def howManyGenes(person):
        if person in one_gene:
            return 1
        if person in two_genes:
            return 2
        return 0
    
    people = set(probabilities.keys())
    for person in people:
        probabilities[person]["gene"][howManyGenes(person)] += p
        probabilities[person]["trait"][person in have_trait] += p

def normalize(probabilities):
    """
    Update `probabilities` such that each probability distribution
    is normalized (i.e., sums to 1, with relative proportions the same).
    """
    people = set(probabilities.keys())
    for person in people:
        total = 0
        for i in range(0, 3):
            total += probabilities[person]["gene"][i]
        for i in range(0, 3):
            probabilities[person]["gene"][i] = probabilities[person]["gene"][i] / total
        
        total = probabilities[person]["trait"][False] + probabilities[person]["trait"][True]

        probabilities[person]["trait"][False] = probabilities[person]["trait"][False] / total
        probabilities[person]["trait"][True] = probabilities[person]["trait"][True] / total


if __name__ == "__main__":
    main()
