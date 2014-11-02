import pygame

def main():
    side_trans = pygame.image.load('side_trans.png')
    corner_trans = pygame.image.load('corner_trans.png')
    bigcorner_trans = pygame.image.load('bigcorner_trans.png')
    
    base_trans = {}
    base_trans[1] = side_trans
    base_trans[2] = pygame.transform.rotate(side_trans, -90)
    base_trans[4] = pygame.transform.rotate(side_trans, -180)
    base_trans[8] = pygame.transform.rotate(side_trans, -270)
    base_trans[16] = corner_trans
    base_trans[32] = pygame.transform.rotate(corner_trans, -90)
    base_trans[64] = pygame.transform.rotate(corner_trans, -180)
    base_trans[128] = pygame.transform.rotate(corner_trans, -270)
    
    index = 1 | 2
    base_trans[index] = bigcorner_trans
    base_trans[index << 1] = pygame.transform.rotate(bigcorner_trans, -90)    
    base_trans[index << 2] = pygame.transform.rotate(bigcorner_trans, -180)
    base_trans[8 | 1] = pygame.transform.rotate(bigcorner_trans, -270)
    
    output = pygame.Surface((200,200), flags=pygame.SRCALPHA, depth=32)
    
    progress = 0
    for i in xrange(256):
        output.fill((0,0,0,0))
        '''j = 1        
        while j <= 128:
            if i & j:
                output.blit(base_trans[j], (0,0))
        
            j = j << 1'''
        for j in base_trans:
            if i & j == j:
                output.blit(base_trans[j], (0,0))
            
            
        filename = "trans/trans_%03d.png" % (i,)
        #print "image trans_%03d %s" % (i, filename)
        pygame.image.save(output, filename)
        
        #if int(i / 25.5) > progress:
        #    progress = int(i / 25.5)
        #    print "Progress %d%%" % (progress*10)


main()
