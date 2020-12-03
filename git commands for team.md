
# Branch strategy

I propose next way of using **git** in our develop:

1. **master** branch is the default branch which always contains last stable version of the game (release)
2. **dev** branch is the main branch with creating new features; when the game version at **dev** will be stable and will have many new features, the teamlead will *merge* **dev** branch into **master** and upload new release
3. each developer has their own branch forked from **dev**
4. each new feature should have it's branch (topic branch), forked from updated branch of the developer who is working on this feature (or it can be forked from existing topic branch)
5. after creating new feature u should merge your main developer branch with the topic branch and create **pull request** to merging your developer branch with **dev**

## Commands

1. Use `git pull` to update your local repository
2. Use `git checkout -b new_feature` to create the branch for concrete new feature and checkout to it
3. Use `git checkout existing_branch` to checkout to existing branch (named **existing_branch**)
4. Use `git push` to push your local changes to global GitHub repository (it works when global repo has this branch)
5. If u created new branch **new_feature**, push it using `git push -u origin new_feature`
6. It's better to merge branches by GitHub a lot, not local


## Simple example

I am new developer and I wanna create **timer** in game. So, the GitHub repository is like this:

```
master -> dev
```

I should create new branch `pasa` (my developer branch) using this code:

```
git checkout dev 
git pull
git checkout -b pasa
```

Firstly, I go to `dev` branch, update it and after that I create `pasa` branch from `dev`. Now my local repository is like this:

```
master -> dev -> pasa
```

Let's create new branch for **timer** feature:

```
git checkout -b timer
```

Now I can change game code to create the timer. After that I commit my changes:

```
git add .
git commit -m 'I have created new timer!'
```

(Don't forget to check your changes)

Okay, I have ways to push my changes:

1. Push `timer` branch to global repo using `git push -u origin timer` and create pull request to `dev`
2. Push `timer` branch to `pasa` using
   ```
   git checkout pasa
   git merge timer
   ```
   and push `pasa` branch to create pull request to `dev`








