DBFilePath = './res/film_db.txt'

#   initialize set
initList = set()

#   read file to list
file = open(DBFilePath, 'r')
for line in file:
    initList.add(int(line.strip()))
file.close()
# print('after add set {}'.format(initList))

#   convert set to list
initList = list(initList)
# print('after convert lisit {}'.format(initList))

#   sort file
initList.sort()
# print('after sort {}'.format(initList))

#   set up for write file
stringForFileList = [ str(element) for element in initList ]

stringForFile = '\n'.join(stringForFileList)

#   write to file
file = open(DBFilePath, 'w')
file.write(stringForFile)
file.close()

print('Finished.')